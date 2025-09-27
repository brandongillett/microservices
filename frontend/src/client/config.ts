// Get the service URL from environment variables or use a default value
export function getServiceUrl(serviceName: string): string {
  const baseUrl = import.meta.env.VITE_API_URL
  if (baseUrl) {
    return `${baseUrl.replace(/\/$/, '')}/${serviceName}`
  }

  // Fallback
  return `http://localhost:8000/${serviceName}`
}

// Configure a service module with base URL and default settings
export function configureService(
  serviceName: string,
  serviceModule: any
): void {
  serviceModule.OpenAPI.BASE = getServiceUrl(serviceName)
  serviceModule.OpenAPI.TIMEOUT = 30000
  serviceModule.OpenAPI.HEADERS = { 'Content-Type': 'application/json' }
}
