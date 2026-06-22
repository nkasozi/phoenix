FROM node:24.0.0-bookworm-slim AS deps
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

FROM node:24.0.0-bookworm-slim AS builder
WORKDIR /app

ARG NEXT_PUBLIC_API_URL=/api
ARG PHOENIX_INTERNAL_API_URL

ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV PHOENIX_INTERNAL_API_URL=$PHOENIX_INTERNAL_API_URL

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

FROM node:24.0.0-bookworm-slim AS runner
WORKDIR /app

ARG PHOENIX_INTERNAL_API_URL

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV PHOENIX_INTERNAL_API_URL=$PHOENIX_INTERNAL_API_URL

COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js ./next.config.js
COPY --from=builder /app/next-env.d.ts ./next-env.d.ts
COPY --from=builder /app/environment.d.ts ./environment.d.ts

EXPOSE 3000

CMD ["./node_modules/.bin/next", "start"]
