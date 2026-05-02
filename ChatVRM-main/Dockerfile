# ============================================
# ChatVRM Docker 多阶段构建配置
# ============================================

# -------------------- 阶段1: 依赖安装 --------------------
FROM node:18-alpine AS deps

WORKDIR /app

# 复制依赖配置文件
COPY package.json package-lock.json* ./

# 安装依赖（包含 devDependencies，确保 Next.js 构建所需的类型声明可用）
#RUN npm install
RUN npm config set registry https://registry.npmmirror.com \
 && npm config set fetch-retry-mintimeout 20000 \
 && npm config set fetch-retry-maxtimeout 120000 \
 && npm install --prefer-offline --no-audit --progress=false

# -------------------- 阶段2: 构建应用 --------------------
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖
COPY --from=deps /app/node_modules ./node_modules

# 复制源代码
COPY . .

# 声明构建参数（从 docker-compose.yml 传入）
ARG NEXT_PUBLIC_DASHSCOPE_KEY
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_WS_URL

# 设置环境变量（构建时）
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_DISABLE_FONT_DOWNLOADS=1 \
    NEXT_FONT_DISABLE_DOWNLOAD=1 \
    NEXT_FONT_IGNORE_ERRORS=true \
    NEXT_PUBLIC_DASHSCOPE_KEY=${NEXT_PUBLIC_DASHSCOPE_KEY} \
    NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    NEXT_PUBLIC_WS_URL=${NEXT_PUBLIC_WS_URL}

# 构建Next.js应用
RUN npm run build

# -------------------- 阶段3: 生产运行 --------------------
FROM node:18-alpine AS runner

WORKDIR /app

# 设置运行时环境变量
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_FONT_DISABLE_DOWNLOAD=1 \
    PORT=3001

# 创建非root用户
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 复制必要文件
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

# Vosk 模型文件将从挂载的 models 文件夹读取，不需要复制到镜像中
# COPY --from=builder /app/public/models ./public/models

# 复制Next.js构建产物
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 切换到非root用户
USER nextjs

# 暴露端口
EXPOSE 3001

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3001/', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# 启动应用
CMD ["node", "server.js"]
