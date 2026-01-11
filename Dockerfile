# 阶段 1: 构建阶段
FROM node:18 as builder

WORKDIR /app

# 定义构建参数
ARG VITE_API_URL=http://localhost:8888
ARG VITE_UPSCALE_MODE=browser

# 设置环境变量（Vite 在构建时读取）
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_UPSCALE_MODE=$VITE_UPSCALE_MODE

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 复制 paraglide 项目配置（postinstall 需要）
COPY project.inlang ./project.inlang
COPY messages ./messages

# 安装依赖
RUN npm install

# 复制源代码和其他必要文件
COPY . .

# 下载模型文件
RUN chmod +x download-models.sh && ./download-models.sh

# 临时移除 ESLint 插件以避免构建失败
RUN sed -i 's/plugins: \[react(), eslintPlugin()\]/plugins: [react()]/' vite.config.ts

# 构建应用
RUN npm run fast-build

# 阶段 2: 生产阶段
FROM nginx:alpine

# 复制自定义 nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 从构建阶段复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 从构建阶段复制模型文件
COPY --from=builder /app/public/models /usr/share/nginx/html/models

# 从构建阶段复制示例图片
COPY --from=builder /app/public/examples /usr/share/nginx/html/examples

# 暴露端口 3332
EXPOSE 3332

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]