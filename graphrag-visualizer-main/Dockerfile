# GraphRAG Visualizer Dockerfile
FROM node:18-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖（包含开发依赖用于构建）
RUN npm ci

# 复制源代码
COPY . .

# 设置环境变量
ENV REACT_APP_API_BASE_URL=http://localhost:8000
ENV TSC_COMPILE_ON_ERROR=true
ENV ESLINT_NO_DEV_ERRORS=true

# 构建应用
RUN npm run build

# 生产阶段 - 使用nginx提供静态文件
FROM nginx:alpine

# 复制构建的文件到nginx
COPY --from=builder /app/build /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 3000

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
