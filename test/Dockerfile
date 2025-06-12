# Trading Bot Premium - Dockerfile
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Trading Bot Premium Team"
LABEL version="1.0.0"
LABEL description="Bot Discord SaaS pour signaux de trading crypto"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=UTC

# Création utilisateur non-root
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Copie des fichiers requirements
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Création des dossiers nécessaires
RUN mkdir -p data logs && \
    chown -R botuser:botuser /app

# Passage à l'utilisateur non-root
USER botuser

# Port d'exposition (pour les webhooks si nécessaire)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sqlite3; sqlite3.connect('data/trading_bot.db').execute('SELECT 1')" || exit 1

# Commande par défaut
CMD ["python3", "main.py"]
