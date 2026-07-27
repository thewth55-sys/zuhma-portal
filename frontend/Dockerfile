# Imagen de PRODUCCIÓN del frontend (la que usa Easypanel).
# En local, docker-compose sobreescribe el CMD con `npm run dev` (montando el código),
# así que este build de prod no estorba al desarrollo.
#
# IMPORTANTE (gotcha de Next.js): las variables NEXT_PUBLIC_* se "hornean" en el
# bundle DURANTE `next build`. En Easypanel deben estar definidas como Environment
# del servicio ANTES de construir, o saldrán vacías en el navegador.

FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
RUN npm run build

FROM node:22-slim AS run
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/next.config.mjs ./next.config.mjs
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["npm", "start"]
