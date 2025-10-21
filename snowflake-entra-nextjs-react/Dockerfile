# syntax=docker/dockerfile:1.7

############################
# 1) Install deps (with cache)
############################
FROM node:20-alpine AS deps
WORKDIR /app

# Needed by sharp / image-optimization on Alpine
RUN apk add --no-cache libc6-compat

# Install dependencies (respect npm lockfile)
COPY package.json package-lock.json* ./
RUN npm ci

############################
# 2) Build the Next.js app
############################
FROM node:20-alpine AS builder
WORKDIR /app

# Copy node_modules from deps stage
COPY .env.production .

COPY --from=deps /app/node_modules ./node_modules

# Copy source

COPY . .

# (Optional) Pass build-time env via --build-arg if you need them during `next build`
# ARG NEXT_PUBLIC_API_BASE=
# ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Ensure standalone output
# You can set this in next.config.js too: { output: 'standalone' }
RUN npx --yes next@15.3.5 build

############################
# 3) Runtime (minimal)
############################
FROM node:20-alpine AS runner
WORKDIR /app

# Alpine runtime helper for sharp
RUN apk add --no-cache libc6-compat

ENV NODE_ENV=production
# App Service injects PORT; default to 3000 for local runs
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
ENV NEXT_TELEMETRY_DISABLED=1

# Copy standalone server & static assets
# - .next/standalone contains the server and the necessary node_modules
# - public and .next/static contain static files
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# If you serve fonts/images from /public, they’re here now.
# No need to copy package.json unless you do runtime installs (we don't).

EXPOSE 3000
CMD ["node", "server.js"]
