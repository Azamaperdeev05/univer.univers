# ==========================================
# STAGE 1: Svelte Client Builder
# ==========================================
FROM node:20-slim AS client-builder

# Install pnpm globally
RUN npm install -g pnpm

WORKDIR /build

# Copy Svelte package configs
COPY univer.client/package.json univer.client/pnpm-lock.yaml* univer.client/package-lock.json* ./

# Install client packages
RUN pnpm install --frozen-lockfile || npm install

# Copy client codebase
COPY univer.client/ ./

# Compile Svelte application (Vite outputs to /static based on outDir: "../static")
RUN pnpm run build || npm run build

# ==========================================
# STAGE 2: Python Backend Server
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY server.py ./
COPY core/ ./core/

# Copy compiled frontend from client-builder stage
COPY --from=client-builder /static ./static

# Copy optional files like VAPID keys
COPY server.py vapid_*.pe[m] ./

# Expose default port (Railway automatically overrides port binding based on PORT env)
EXPOSE 7435

# Start the python backend server
CMD ["python", "server.py"]

