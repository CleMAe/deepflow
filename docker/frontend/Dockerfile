FROM nginx:1.25-alpine

COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/frontend/index.html /usr/share/nginx/html/index.html

EXPOSE 80
