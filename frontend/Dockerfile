# ---------- Stage 1: build the React app ----------
FROM node:25-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# ---------- Stage 2: serve static files with unprivileged Nginx ----------
# nginx-unprivileged runs as uid 101 and listens on 8080 (no root required).
FROM nginxinc/nginx-unprivileged:1.30-alpine
# Pull in Alpine security patches released after the base image was built.
USER root
RUN apk upgrade --no-cache
ENV BACKEND_URL=http://backend:8000
COPY --from=build /app/dist /usr/share/nginx/html
# Templates under /etc/nginx/templates are rendered with envsubst at startup.
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget -qO- http://127.0.0.1:8080/healthz >/dev/null || exit 1
USER 101
