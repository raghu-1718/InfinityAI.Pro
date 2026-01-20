# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy root tsconfig and package.json
COPY tsconfig.base.json ./
COPY frontend/web-app/tsconfig.json ./
COPY frontend/web-app/package*.json ./

# Install dependencies with retry logic for Cloud Build
RUN npm install --legacy-peer-deps 2>&1 | tail -20 || npm install --legacy-peer-deps --force 2>&1 | tail -20

# Copy source code
COPY frontend/web-app/ .

# Build the Next.js app
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install dumb-init to handle signals properly
RUN apk add --no-cache dumb-init

# Copy package.json for production dependencies
COPY frontend/web-app/package*.json ./

# Install only production dependencies
RUN npm install --legacy-peer-deps --production 2>&1 | tail -20 || npm install --legacy-peer-deps --production --force 2>&1 | tail -20

# Copy built app from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

# Expose port 3000
EXPOSE 3000

# Set NODE_ENV to production
ENV NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})" || exit 1

# Use dumb-init to properly handle signals
ENTRYPOINT ["/sbin/dumb-init", "--"]

# Start Next.js production server
CMD ["npm", "start"]
