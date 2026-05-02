# Multi-stage build for manage-system

# Stage 1: Build Vue application
FROM node:16-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with npm mirror and aggressive retry
RUN npm config set registry https://registry.npmmirror.com \
    && npm config set fetch-retry-mintimeout 20000 \
    && npm config set fetch-retry-maxtimeout 120000 \
    && npm config set fetch-retries 10 \
    && npm config set maxsockets 1 \
    && rm -f package-lock.json \
    && npm install --legacy-peer-deps || \
    (npm config set registry https://registry.npm.taobao.org && npm install --legacy-peer-deps) || \
    (npm config set registry https://registry.npmjs.org && npm install --legacy-peer-deps)

# Copy source code
COPY . .

# Build for production
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

