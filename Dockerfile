FROM node:24-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --omit=dev

COPY server.js login.html seed_data.json taxonomy.json ./
COPY public ./public

RUN addgroup -S app && adduser -S app -G app \
  && mkdir -p /app/data && chown -R app:app /app

ENV NODE_ENV=production
ENV PORT=3000
ENV DB_PATH=/app/data/cowhand.sqlite
VOLUME /app/data
EXPOSE 3000

USER app
CMD ["node", "server.js"]
