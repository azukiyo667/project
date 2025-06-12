# Copilot Instructions pour Trading Bot Premium

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Context du Projet

Ce projet est un **Bot Discord de Trading Crypto Premium** conçu pour être vendu comme service SaaS rentable. Le bot fournit des signaux de trading automatisés, des analyses techniques avancées et des fonctionnalités de portfolio management.

## Architecture

### Structure des Modules
- **main.py**: Point d'entrée principal du bot Discord
- **src/trading/**: Logique d'analyse technique et génération de signaux
- **src/database/**: Gestion de la base de données SQLite
- **src/commands/**: Commandes Discord organisées par catégorie
- **src/utils/**: Utilitaires (permissions, helpers)

### Fonctionnalités Principales
1. **Analyse Technique**: RSI, MACD, Bollinger Bands, EMA, Stochastic, ADX
2. **Signaux de Trading**: Génération automatique avec niveaux de confiance
3. **Système d'Abonnements**: Free, Premium, VIP avec fonctionnalités différenciées
4. **Portfolio Management**: Suivi des positions, calcul P&L, alertes
5. **Machine Learning**: Intégration RandomForest pour prédictions

## Guidelines de Développement

### Style de Code
- Utiliser des **type hints** pour toutes les fonctions
- Documenter les fonctions complexes avec des docstrings
- Gérer les exceptions avec des try/catch appropriés
- Logger les erreurs importantes
- Utiliser des noms de variables explicites en français ou anglais

### Base de Données
- Utiliser le `DatabaseManager` pour toutes les opérations DB
- Toujours vérifier les permissions avant les opérations sensibles
- Logger les activités utilisateur importantes

### Discord Bot
- Utiliser les **slash commands** (app_commands) de préférence
- Créer des embeds visuellement attractifs
- Implémenter des boutons d'interaction pour l'UX
- Respecter les limites de Discord (embeds, messages, etc.)

### Monétisation
- **Tier System**: Free (limité) → Premium (standard) → VIP (premium)
- **Fonctionnalités Premium**: Analyses avancées, portfolio, alertes
- **Codes Promo**: Système de réduction pour acquisition clients
- **Métriques**: Tracker utilisation pour optimiser conversions

### Sécurité
- Valider toutes les entrées utilisateur
- Utiliser des variables d'environnement pour les secrets
- Implémenter une authentification admin robuste
- Ne jamais exposer d'API keys dans les logs

## Business Model

### Pricing Strategy
- **Free**: 10 signaux/jour, timeframes limités → acquisition
- **Premium** ($29.99/mois): 100 signaux/jour, analyses complètes → volume
- **VIP** ($79.99/mois): Illimité, features exclusives → rentabilité

### Fonctionnalités de Conversion
- Prompts d'upgrade réguliers mais non intrusifs
- Démonstration de valeur avant paywall
- Codes promo pour inciter à l'essai
- Support premium pour fidélisation

## Performance & Scalabilité

### Optimisations
- Cache des permissions (5 min)
- Batch des analyses pour réduire les appels API
- Nettoyage automatique des données anciennes
- Monitoring des performances système

### Limitations Actuelles
- Une seule instance de bot (pas de clustering)
- Base SQLite (migration PostgreSQL recommandée pour scale)
- Simulation des prix crypto (intégrer vraies APIs)

## Maintenance

### Tâches Automatiques
- Analyse marché toutes les 5 minutes
- Mise à jour portfolios toutes les heures
- Rapport quotidien automatique
- Nettoyage DB tous les 90 jours

### Monitoring
- Logs applicatifs détaillés
- Statistiques d'utilisation par user
- Métriques de performance des signaux
- Health checks système

## Instructions Spécifiques pour Copilot

1. **Toujours vérifier les permissions** avant d'ajouter des fonctionnalités premium
2. **Créer des embeds Discord attractifs** pour chaque réponse utilisateur
3. **Implémenter la logique business** (limites par tier, encouragement upgrade)
4. **Prioriser l'UX** et la conversion vers les plans payants
5. **Maintenir la qualité des signaux** car c'est le produit principal
6. **Logger les actions importantes** pour le business intelligence

## Variables d'Environnement Requises

```env
DISCORD_TOKEN=
BINANCE_API_KEY=
BINANCE_SECRET_KEY=
ALERT_CHANNEL_ID=
PREMIUM_CHANNEL_ID=
VIP_CHANNEL_ID=
PREMIUM_ROLE_ID=
VIP_ROLE_ID=
ADMIN_ROLE_ID=
```

## Déploiement

Le bot est conçu pour être déployé sur VPS/Cloud avec:
- Python 3.10+
- Dépendances dans requirements.txt
- Variables d'environnement configurées
- Monitoring et auto-restart

## Objectif Commercial

Créer un service SaaS rentable générant des revenus récurrents grâce à:
- Signaux de trading de qualité
- Fonctionnalités premium attractives
- Expérience utilisateur excellente
- Support et communauté engagée
