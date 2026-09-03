# ---------- Stage 1: build ----------
# Installs every dependency, including anything needed only to build.
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json ./
RUN npm install
COPY server.js ./

# ---------- Stage 2: production ----------
# Starts from a clean base and takes only what is needed to run.
FROM node:20-alpine AS production

WORKDIR /app
COPY --from=builder /app/package.json ./
RUN npm install --omit=dev
COPY --from=builder /app/server.js ./

EXPOSE 3000
CMD ["npm", "start"]
