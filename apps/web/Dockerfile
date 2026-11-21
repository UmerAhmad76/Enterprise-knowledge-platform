# Build context is apps/web itself (unlike the api/worker images), since the
# frontend has no dependency on packages/core.
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Vite bakes these into the JS bundle at BUILD time, not at container start time.
# Changing them later means rebuilding the image, not just restarting the container.
ARG VITE_API_URL=http://localhost:8000
ARG VITE_USE_DEMO=false
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_USE_DEMO=$VITE_USE_DEMO
RUN npm run build

# Second stage: a tiny server for the built static files, so the final image
# doesn't carry Node, npm, or any source code.
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80