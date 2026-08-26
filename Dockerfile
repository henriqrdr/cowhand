FROM node:24-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --omit=dev

COPY server.js index.html seed_data.json ./

ENV PORT=3000
ENV DB_PATH=/app/data/cowhand.sqlite
VOLUME /app/data
EXPOSE 3000

CMD ["node", "server.js"]
