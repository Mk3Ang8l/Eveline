# Use the official Microsoft Playwright image
FROM mcr.microsoft.com/playwright:v1.57.0-noble


WORKDIR /app

# This Dockerfile is designed to be run with the repo ROOT as the build context.
# In Render, set 'Dockerfile Path' to: playwright-service/Dockerfile
# And keep 'Build Context' as the default (root of the repo).

COPY playwright-service/package*.json ./
RUN npm install

COPY playwright-service/ .

# Ensure server.js is at the root of /app for the CMD below
EXPOSE 3000

CMD ["node", "server.js"]



