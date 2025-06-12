#!/bin/bash

# Script de démarrage pour Trading Bot Premium
# Usage: ./start.sh [dev|prod]

set -e

# Configuration
VENV_PATH="./crypto_trading_bot"
BOT_SCRIPT="main.py"
MODE="${1:-dev}"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Trading Bot Premium - Démarrage${NC}"
echo -e "${BLUE}===========================================${NC}"

# Vérification de l'environnement virtuel
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Environnement virtuel non trouvé!${NC}"
    echo -e "${YELLOW}Création de l'environnement virtuel...${NC}"
    python3 -m venv crypto_trading_bot
fi

# Activation de l'environnement virtuel
echo -e "${YELLOW}📦 Activation de l'environnement virtuel...${NC}"
source "$VENV_PATH/bin/activate"

# Installation/Mise à jour des dépendances
echo -e "${YELLOW}🔧 Installation des dépendances...${NC}"
pip install -r requirements.txt

# Vérification du fichier .env
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Fichier .env manquant!${NC}"
    echo -e "${YELLOW}Copie du fichier .env.example vers .env${NC}"
    cp .env.example .env
    echo -e "${RED}⚠️  Veuillez configurer le fichier .env avec vos tokens!${NC}"
    exit 1
fi

# Création des dossiers nécessaires
mkdir -p data logs

# Configuration du mode
if [ "$MODE" = "prod" ]; then
    echo -e "${GREEN}🏭 Mode Production${NC}"
    export DEBUG_MODE=false
    export LOG_LEVEL=WARNING
else
    echo -e "${YELLOW}🔧 Mode Développement${NC}"
    export DEBUG_MODE=true
    export LOG_LEVEL=INFO
fi

# Vérification de la connectivité
echo -e "${YELLOW}🌐 Vérification de la connectivité...${NC}"
python3 -c "import requests; requests.get('https://api.binance.com/api/v3/ping', timeout=5); print('✅ Binance API accessible')" 2>/dev/null || echo -e "${RED}❌ Problème de connectivité Binance${NC}"

# Démarrage du bot
echo -e "${GREEN}🎯 Démarrage du Trading Bot...${NC}"
echo -e "${BLUE}===========================================${NC}"

# Gestion des signaux pour arrêt propre
trap 'echo -e "\n${YELLOW}⏹️  Arrêt du bot...${NC}"; kill $BOT_PID 2>/dev/null; exit 0' INT TERM

# Démarrage avec restart automatique en cas de crash
while true; do
    python3 "$BOT_SCRIPT" &
    BOT_PID=$!
    wait $BOT_PID

    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ Bot arrêté proprement${NC}"
        break
    else
        echo -e "${RED}💥 Bot crashé (code: $EXIT_CODE)${NC}"
        echo -e "${YELLOW}🔄 Redémarrage dans 5 secondes...${NC}"
        sleep 5
    fi
done

echo -e "${BLUE}👋 Trading Bot Premium arrêté${NC}"
