# Local-dev Dockerfile. Production deployment is via Vercel (no Dockerfile
# involved). The container runs `next dev` so NEXT_PUBLIC_* env vars from
# docker-compose are read at runtime — `next start` would require build-time
# env vars baked into the bundle.

FROM node:20-alpine
WORKDIR /app

COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .

EXPOSE 3000
ENV PORT=3000 HOSTNAME=0.0.0.0
CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0"]
