FROM node:22-alpine
# Install deps at /app so they're accessible to shared/auth.js
WORKDIR /app
COPY docker/yjs/package*.json ./
RUN npm install --omit=dev
# Preserve directory structure: index.js at /app/docker/yjs/, shared at /app/shared/
COPY docker/yjs/index.js docker/yjs/
COPY shared/ shared/
WORKDIR /app/docker/yjs
EXPOSE 1234
HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD wget -q -O- http://localhost:1234/health || exit 1
CMD ["node", "index.js"]
