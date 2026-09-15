# ==============================================================================
# SIH1518 — Frontend Dockerfile (Multi-Stage Production Build with Nginx)
# ==============================================================================

# Stage 1: Build static assets with Node.js
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code and build production bundle
COPY . .
RUN npm run build

# Stage 2: Serve static production assets with Nginx
FROM nginx:alpine AS runner

# Default simple Nginx config for SPA
RUN rm -rf /etc/nginx/conf.d/*
RUN printf 'server {\n\
    listen 80;\n\
    server_name localhost;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    location /api/ {\n\
        proxy_pass http://backend:8000/api/;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

# Copy compiled static HTML/CSS/JS from builder
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
