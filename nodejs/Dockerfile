# Stage 1: Build
FROM node:18-alpine AS builder
WORKDIR /app

# 1. Copy dependency definitions 
COPY package*.json ./

# 2. Install all dependencies inside the container
RUN npm install

# 3. Copy all source code 
COPY . .

# 4. Build the application using npx to safely find the nest binary
RUN npx nest build

# Stage 2: Production
FROM node:18-alpine
WORKDIR /app

# 5. Set environment variable for the client 
ENV NODE_ENV=production

# 6. Copy only the production build and node_modules 
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./

EXPOSE 3000

# 7. Start the app in production mode
CMD ["npm", "run", "start:prod"]
