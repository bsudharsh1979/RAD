FROM node:22-alpine AS deps
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web ./
RUN npm run build

FROM node:22-alpine
WORKDIR /web
COPY --from=deps /web ./
ENV PORT=3000
EXPOSE 3000
CMD ["npm", "run", "start"]
