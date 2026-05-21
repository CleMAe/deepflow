# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package.json ./
RUN npm config set registry https://registry.npmmirror.com && \
    rm -f package-lock.json && npm install

COPY frontend/ .

ARG VITE_API_BASE_URL=/api/v1
ARG VITE_ENABLE_MSW=false
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_ENABLE_MSW=$VITE_ENABLE_MSW

RUN npm run build

# Production stage
FROM nginx:1.25-alpine

COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
