# ---- build stage: Node compiles the JSX into a static bundle ----
FROM node:20-alpine AS build

WORKDIR /app
COPY package.json ./
RUN npm install

COPY index.html ./
COPY src ./src
RUN npm run build

# ---- run stage: only the built static files ship, no Node ----
FROM nginx:alpine

COPY --from=build /app/dist/bundle.js /usr/share/nginx/html/bundle.js
COPY --from=build /app/index.html     /usr/share/nginx/html/index.html

EXPOSE 80
