FROM node:22-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 3000

# Dev por defecto (docker-compose usa `npm run dev`).
# Para producción en Easypanel: `npm run build` y luego `npm start`.
CMD ["npm", "run", "dev"]
