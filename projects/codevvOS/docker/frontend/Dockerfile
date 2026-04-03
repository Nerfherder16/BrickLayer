FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD wget -q -O- http://localhost:3000 || exit 1
CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "3000"]
