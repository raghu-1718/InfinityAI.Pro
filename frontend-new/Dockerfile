# Stage 1: Build
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
# Install only prod deps for runtime, then add dev deps for build
RUN npm ci --omit=dev && npm install --only=dev --no-audit --no-fund

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Stage 2: Production with NGINX
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built app from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 8080
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
