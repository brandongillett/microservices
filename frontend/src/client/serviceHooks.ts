import { useMutation, type UseMutationOptions } from '@tanstack/react-query'
import { loadService } from './services'

export function useServiceMutation<TData = any, TError = any, TVariables = any>(
  serviceName: string,
  methodName: string,
  options?: UseMutationOptions<TData, TError, TVariables>
) {
  return useMutation<TData, TError, TVariables>({
    mutationFn: async (variables: TVariables) => {
      const serviceClient = await loadService(serviceName)

      if (!serviceClient) {
        throw new Error('Service unavailable. Please try again later.')
      }

      const serviceMethod = findServiceMethod(
        serviceClient,
        methodName,
        serviceName
      )
      return serviceMethod(variables)
    },
    ...options,
  })
}

export function transformApiError(error: any) {
  console.log('transformApiError - Raw error:', error)
  console.log('transformApiError - Error JSON:', JSON.stringify(error, null, 2))
  console.log('transformApiError - Error name:', error.name)
  console.log('transformApiError - Error body:', error.body)
  console.log('transformApiError - Error message:', error.message)

  let errorMessage = 'An Error has Occurred'

  // Extract detail from API error
  if (error.name === 'ApiError' && error.body?.detail) {
    errorMessage = error.body.detail
    console.log('Using error.body.detail:', errorMessage)
  } else if (error.response?.data?.detail) {
    errorMessage = error.response.data.detail
    console.log('Using error.response.data.detail:', errorMessage)
  } else if (error.message && error.message !== 'Failed to fetch') {
    errorMessage = error.message
    console.log('Using error.message:', errorMessage)
  }

  return {
    name: 'ApiError',
    message: errorMessage,
    status: error.status || error.response?.status,
    originalError: error,
  }
}

// Helper to find the correct method in the service client
function findServiceMethod(
  serviceClient: any,
  methodName: string,
  serviceName: string
): Function {
  for (const [key, serviceClass] of Object.entries(serviceClient)) {
    if (key.endsWith('Service')) {
      if (typeof serviceClass === 'function') {
        const ServiceClass = serviceClass as any
        if (typeof ServiceClass[methodName] === 'function') {
          return ServiceClass[methodName]
        }
      }

      // Check for instance methods
      if (typeof serviceClass === 'object' && serviceClass !== null) {
        const service = serviceClass as any
        if (typeof service[methodName] === 'function') {
          return service[methodName]
        }
      }
    }
  }

  const availableMethods = getAvailableMethods(serviceClient)
  const errorMessage = `Method '${methodName}' not found in service '${serviceName}'.${
    availableMethods.length > 0
      ? ` Available methods: ${availableMethods.join(', ')}`
      : ' No methods found.'
  }`

  throw new Error(errorMessage)
}

function getAvailableMethods(serviceClient: any): string[] {
  const methods: string[] = []

  for (const [key, serviceClass] of Object.entries(serviceClient)) {
    if (key.endsWith('Service') && typeof serviceClass === 'function') {
      const staticMethods = Object.getOwnPropertyNames(serviceClass)
        .filter((name) => typeof (serviceClass as any)[name] === 'function')
        .filter((name) => name !== 'constructor')

      methods.push(...staticMethods)
    }
  }

  return methods
}
