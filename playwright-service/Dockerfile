FROM mcr.microsoft.com/playwright:v1.57.0-noble

WORKDIR /app

COPY package*.json ./
RUN rm -f package-lock.json
RUN npm install
RUN npx playwright install chromium

COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
