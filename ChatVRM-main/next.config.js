/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 通过环境变量注入 basePath，生产部署在 /chat 路径下
  assetPrefix: process.env.BASE_PATH || "",
  basePath: process.env.BASE_PATH || "",
  trailingSlash: true,
  publicRuntimeConfig: {
    root: process.env.BASE_PATH || "",
  },
  // Docker部署优化：生成独立输出
  output: 'standalone',
  
  // 支持 vosk-browser 和 WebAssembly
  webpack: (config, { isServer }) => {
    // 解决 vosk-browser 依赖问题
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      path: false,
      crypto: false,
    };
    
    // 支持 WebAssembly
    config.experiments = {
      ...config.experiments,
      asyncWebAssembly: true,
      layers: true,
    };
    
    // 处理 .wasm 文件
    config.module.rules.push({
      test: /\.wasm$/,
      type: 'webassembly/async',
    });
    
    return config;
  },
  
  // 允许访问 public 目录下的大文件
  async headers() {
    return [
      {
        source: '/models/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
