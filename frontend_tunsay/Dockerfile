FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend_tunsay/package*.json ./
RUN npm ci

COPY frontend_tunsay ./
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

COPY frontend_tunsay/package*.json ./
RUN npm ci --only=production

COPY --from=builder /app/dist ./dist

EXPOSE 3000
CMD ["node", "dist/server.cjs"]
