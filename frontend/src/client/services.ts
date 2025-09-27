import { configureService } from './config'

const services = new Map<string, any>()
const serviceLoadingPromises = new Map<string, Promise<any>>()

// Import service modules
const serviceModules = import.meta.glob('./**/index.ts', { eager: false })

export async function loadService(serviceName: string): Promise<any> {
  if (services.has(serviceName)) {
    return services.get(serviceName)
  }

  if (serviceLoadingPromises.has(serviceName)) {
    return serviceLoadingPromises.get(serviceName)
  }

  const servicePath = `./${serviceName}/index.ts`
  const importFn = serviceModules[servicePath]

  if (!importFn) {
    throw new Error('Unable to connect to server. Please try again later.')
  }

  const loadingPromise = (async () => {
    try {
      const serviceModule = await importFn()
      configureService(serviceName, serviceModule)
      services.set(serviceName, serviceModule)

      return serviceModule
    } catch (error) {
      throw new Error(
        'Unable to connect to server. Please check your connection and try again.'
      )
    } finally {
      serviceLoadingPromises.delete(serviceName)
    }
  })()

  serviceLoadingPromises.set(serviceName, loadingPromise)
  return loadingPromise
}

export async function getService(serviceName: string) {
  return await loadService(serviceName)
}

export function getServiceClient(serviceName: string): any {
  const service = services.get(serviceName)
  if (!service) {
    throw new Error('Service temporarily unavailable. Please try again later.')
  }
  return service
}

export function getRegisteredServices(): string[] {
  return Array.from(services.keys())
}
