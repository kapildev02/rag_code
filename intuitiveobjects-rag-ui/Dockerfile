
FROM node:20

WORKDIR /app

COPY package*.json ./
RUN npm install

# Copy env first, then code (better for layer caching)
COPY .env .env
COPY . .

# Build Vite React app with env vars injected
RUN npm run build

# Serve with nginx or other static server
RUN npm install -g serve

EXPOSE 3030
CMD ["serve", "-s", "dist", "-l", "3030"]

