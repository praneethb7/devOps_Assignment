FROM node:20-alpine

WORKDIR /app

# copy the manifest first so `npm install` is cached unless deps change
COPY package.json ./
RUN npm install --omit=dev

COPY server.js ./

EXPOSE 3000
CMD ["node", "server.js"]
