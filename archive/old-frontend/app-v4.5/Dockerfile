# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps
COPY . .
# Ensure Vite envs are available during build (can be overridden at build time)
ARG VITE_ENGINE_A_URL
ARG VITE_ENGINE_B_URL
ARG VITE_ENGINE_C_URL
ARG VITE_ENGINE_D_URL
ARG VITE_APP_NAME
ARG VITE_REFRESH_INTERVAL
ARG VITE_WS_RECONNECT_INTERVAL
ARG VITE_GCP_PROJECT_ID
ARG VITE_GCP_REGION
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
