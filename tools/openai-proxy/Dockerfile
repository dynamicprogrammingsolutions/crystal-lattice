ARG NODE_IMAGE=node:22-alpine
FROM ${NODE_IMAGE}

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY proxy.js proxy_args.js proxy_config.js rate_limit.js ./

USER node

ENTRYPOINT ["node", "/app/proxy.js"]