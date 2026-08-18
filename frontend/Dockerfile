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

# Las NEXT_PUBLIC_* se hornean en el bundle durante `next build`, así que deben
# existir como ENV en ESTE punto. Easypanel las inyecta como --build-arg; aquí las
# declaramos (ARG) y las promovemos a ENV para que `npm run build` las vea.
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_ODOO_LIVECHAT_URL
ARG NEXT_PUBLIC_ODOO_LIVECHAT_CHANNEL
ARG NEXT_PUBLIC_TURNSTILE_SITE_KEY
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY \
    NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_ODOO_LIVECHAT_URL=$NEXT_PUBLIC_ODOO_LIVECHAT_URL \
    NEXT_PUBLIC_ODOO_LIVECHAT_CHANNEL=$NEXT_PUBLIC_ODOO_LIVECHAT_CHANNEL \
    NEXT_PUBLIC_TURNSTILE_SITE_KEY=$NEXT_PUBLIC_TURNSTILE_SITE_KEY

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
