# ============ 构建阶段 ============
FROM node:18-alpine AS build-stage

WORKDIR /app/static/vue_app

# 复制 package 文件
COPY app/static/vue_app/package*.json ./

# 配置 npm 使用淘宝镜像源
RUN npm config set registry https://registry.npmmirror.com

# 安装所有依赖
RUN npm install

# 复制源代码
COPY app/static/vue_app ./
COPY teacher/frontend /teacher/frontend

# 构建生产版本
RUN node node_modules/@vue/cli-service/bin/vue-cli-service.js build

# ============ 生产阶段 ============
FROM nginx:alpine AS production-stage

# 复制 nginx 配置
COPY app/static/vue_app/nginx.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制构建产物
COPY --from=build-stage /app/static/vue_app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
