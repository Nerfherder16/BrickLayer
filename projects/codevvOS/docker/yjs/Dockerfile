FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 1234
HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD curl -f http://localhost:1234/health || exit 1
CMD ["node", "index.js"]
