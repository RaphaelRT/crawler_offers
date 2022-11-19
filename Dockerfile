FROM node:12-alpine AS BUILD_IMAGE
ENV NODE_ENV=production
#RUN apk update && apk add python make g++ && rm -rf /var/cache/apk/*
WORKDIR /usr/src/app
COPY package*.json ./
RUN npm install --production
COPY . .
RUN npm run build


FROM node:12-alpine
COPY --from=BUILD_IMAGE /usr/src/app/node_modules ./node_modules
COPY --from=BUILD_IMAGE /usr/src/app/build ./build
COPY --from=BUILD_IMAGE /usr/src/app/package*.json  ./
COPY expressRouter.js ./
COPY .env ./
EXPOSE 5000
CMD ["npm", "run", "serv"]