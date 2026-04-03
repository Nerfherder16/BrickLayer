FROM node:22-alpine
RUN apk add --no-cache python3 make g++ && npm install -g node-gyp
WORKDIR /app
COPY docker/ptyhost/package.json ./
RUN npm install --omit=dev
COPY docker/ptyhost/index.js ./docker/ptyhost/
COPY shared/ shared/
WORKDIR /app/docker/ptyhost
EXPOSE 3001
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD wget -q -O- http://127.0.0.1:3001/health || exit 1
CMD ["node", "index.js"]
