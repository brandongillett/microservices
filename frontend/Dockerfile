FROM node:20 AS build-stage

WORKDIR /app

COPY package*.json /app/

RUN npm install

# Set the VITE_API_URL variable at build time
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

COPY ./ /app/

RUN npm run build


FROM nginx:1

COPY --from=build-stage /app/dist/ /usr/share/nginx/html

COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY ./nginx-backend-not-found.conf /etc/nginx/extra-conf.d/backend-not-found.conf
