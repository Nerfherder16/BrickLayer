FROM nginx:alpine
RUN apk add --no-cache openssl curl && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/nginx.key \
    -out /etc/ssl/certs/nginx.crt \
    -subj "/CN=codevvos-lan/O=CodeVV/C=US"
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 443
HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD curl -f -k https://localhost/health || exit 1
CMD ["nginx", "-g", "daemon off;"]
