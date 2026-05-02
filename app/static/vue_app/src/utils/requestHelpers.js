export function normalizeRequestConfig(config = {}) {
  const nextConfig = { ...config }
  const headers = { ...(nextConfig.headers || {}) }

  if (typeof FormData !== 'undefined' && nextConfig.data instanceof FormData) {
    delete headers['Content-Type']
    delete headers['content-type']
  }

  nextConfig.headers = headers
  return nextConfig
}
