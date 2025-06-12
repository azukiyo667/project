# 🚀 Guide de Déploiement Rapide - Trading Bot Premium

## 📋 Prérequis

### Développement Local
- Python 3.10+ installé
- Git installé
- Un compte Discord Developer

### Production
- Docker & Docker Compose installés
- Serveur VPS/Cloud (minimum 1GB RAM)
- Nom de domaine (optionnel pour webhooks)

## 🔧 Installation Locale

### 1. Clonage et Setup
```bash
git clone <votre-repo>
cd trading-bot-premium

# Création environnement virtuel
python3 -m venv crypto_trading_bot
source crypto_trading_bot/bin/activate

# Installation dépendances
pip install -r requirements.txt
```

### 2. Configuration Discord

#### Créer une Application Discord
1. Aller sur https://discord.com/developers/applications
2. Cliquer "New Application"
3. Nommer votre bot (ex: "Trading Bot Premium")
4. Aller dans "Bot" → "Add Bot"
5. Copier le token dans `.env`

#### Inviter le Bot sur votre Serveur
```
https://discord.com/api/oauth2/authorize?client_id=VOTRE_CLIENT_ID&permissions=8&scope=bot%20applications.commands
```

#### Configuration des Rôles et Canaux
1. Créer les rôles: `Premium`, `VIP`, `Admin`
2. Créer les canaux: `#alerts`, `#premium-signals`, `#vip-signals`
3. Noter les IDs dans `.env`

### 3. Configuration Environment
```bash
# Copier le template
cp .env.example .env

# Éditer avec vos valeurs
nano .env
```

**Variables obligatoires:**
- `DISCORD_TOKEN` - Token de votre bot
- `ALERT_CHANNEL_ID` - ID du canal alerts
- `PREMIUM_ROLE_ID` - ID du rôle Premium
- `VIP_ROLE_ID` - ID du rôle VIP

### 4. Test et Démarrage
```bash
# Test de configuration
python3 test_setup.py

# Démarrage du bot
./start.sh
```

## 🏭 Déploiement Production

### Option 1: Docker Simple
```bash
# Build et démarrage
docker-compose up -d

# Vérification logs
docker-compose logs -f trading-bot
```

### Option 2: Docker avec PostgreSQL
```bash
# Démarrage avec base PostgreSQL
docker-compose --profile production up -d

# Migration des données
docker-compose exec trading-bot python3 migrate_to_postgres.py
```

### Option 3: VPS Manuel
```bash
# Sur votre serveur
git clone <votre-repo>
cd trading-bot-premium

# Installation Python et dépendances
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y

# Setup environnement
python3 -m venv crypto_trading_bot
source crypto_trading_bot/bin/activate
pip install -r requirements.txt

# Configuration service systemd
sudo cp deploy/trading-bot.service /etc/systemd/system/
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

## 🔐 Sécurité Production

### Variables d'Environnement Critiques
```bash
# Génération de clés sécurisées
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Configuration base de données sécurisée
DATABASE_URL=postgresql://user:$(openssl rand -base64 12)@localhost/trading_bot
```

### Firewall
```bash
# Ubuntu/Debian
sudo ufw allow 22    # SSH
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### SSL/TLS (pour webhooks)
```bash
# Avec Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com
```

## 📊 Monitoring

### Logs
```bash
# Logs en temps réel
docker-compose logs -f trading-bot

# Ou pour installation manuelle
tail -f logs/bot.log
```

### Monitoring Avancé (Optionnel)
```bash
# Démarrage avec monitoring
docker-compose --profile monitoring up -d

# Accès interfaces
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
```

## 🔄 Maintenance

### Mise à jour du Bot
```bash
# Arrêt propre
docker-compose down

# Mise à jour code
git pull

# Redémarrage
docker-compose up -d
```

### Backup Base de Données
```bash
# SQLite
cp data/trading_bot.db backup/trading_bot_$(date +%Y%m%d).db

# PostgreSQL
docker-compose exec postgres pg_dump -U botuser trading_bot > backup/db_$(date +%Y%m%d).sql
```

### Nettoyage
```bash
# Nettoyage logs anciens (>30 jours)
find logs/ -name "*.log" -mtime +30 -delete

# Nettoyage données anciennes
python3 scripts/cleanup_old_data.py
```

## 🚨 Dépannage

### Bot ne démarre pas
1. Vérifier `.env` (token Discord valide)
2. Vérifier permissions bot sur Discord
3. Vérifier logs: `docker-compose logs trading-bot`

### Signaux ne s'affichent pas
1. Vérifier IDs canaux dans `.env`
2. Vérifier permissions bot sur les canaux
3. Vérifier rôles utilisateurs

### Performance
1. Surveiller CPU/RAM: `docker stats`
2. Optimiser requêtes base de données
3. Ajouter cache Redis si nécessaire

## 💰 Monétisation

### Configuration Stripe (Paiements)
1. Créer compte Stripe
2. Récupérer clés API dans `.env`
3. Configurer webhooks pour gestion abonnements

### Gestion Abonnements
```bash
# Commandes admin
/admin_add_premium @utilisateur 30  # 30 jours premium
/admin_stats                        # Statistiques
/admin_broadcast "Message à tous"   # Communication
```

---

**🎉 Votre Trading Bot Premium est maintenant déployé !**

Pour support: créer une issue GitHub ou contacter l'équipe de développement.
