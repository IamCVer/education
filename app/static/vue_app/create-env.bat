@echo off
echo Creating .env file for local development...

(
echo # 本地开发环境配置
echo VITE_API_BASE=http://localhost:8000/api/v1
echo VITE_WS_BASE=ws://localhost:8000
echo VITE_MIND_ASSIST_URL=http://localhost:3001
echo VITE_GRAPH_URL=http://localhost:3000
) > .env

echo .env file created successfully!

echo.
echo Creating .env.docker file for Docker deployment...

(
echo # Docker 部署环境配置
echo VITE_API_BASE=http://localhost:8000/api/v1
echo VITE_WS_BASE=ws://localhost:8000
echo VITE_MIND_ASSIST_URL=http://localhost:3001
echo VITE_GRAPH_URL=http://localhost:3000
) > .env.docker

echo .env.docker file created successfully!

echo.
echo Creating .env.production file for production...

(
echo # 生产环境配置 - 请根据实际域名修改
echo VITE_API_BASE=/api/v1
echo VITE_WS_BASE=ws://your-domain.com
echo VITE_MIND_ASSIST_URL=http://your-domain.com:3001
echo VITE_GRAPH_URL=http://your-domain.com:3000
) > .env.production

echo .env.production file created successfully!
echo.
echo Done! Environment files created:
echo   - .env (local development)
echo   - .env.docker (Docker deployment)
echo   - .env.production (production deployment)
echo.
echo You can now run: npm install
pause

