FROM node:22-alpine
# TIME_BOMB: Must use node:22-alpine, NOT node-alpine (unpinned). node-pty requires node-gyp.
RUN apk add --no-cache python3 make g++ && npm install -g node-gyp
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 3001
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD wget -q -O- http://localhost:3001/health || exit 1
CMD ["node", "index.js"]
