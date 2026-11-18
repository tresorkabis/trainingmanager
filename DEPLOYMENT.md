# Déploiement Docker

## Préparer la configuration

Copiez le modèle, puis définissez des secrets uniques et forts :

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Collez une clé générée dans `DJANGO_SECRET_KEY` et un mot de passe fort dans
`POSTGRES_PASSWORD`. Remplacez aussi `ALLOWED_HOSTS` par le nom DNS/IP utilisé
pour joindre l'application. Pour un accès HTTPS, renseignez
`CSRF_TRUSTED_ORIGINS`, par exemple `https://formation.example.com`.

## Démarrer

Depuis le répertoire du projet :

```bash
docker compose up --build -d
docker compose logs -f web
```

L'application est disponible sur `http://localhost:8000` par défaut. Au
démarrage, le conteneur attend que PostgreSQL soit sain, applique les
migrations, collecte les fichiers statiques et lance Gunicorn.

Créer le compte administrateur de façon interactive :

```bash
docker compose exec web python manage.py createsuperuser
```

Arrêter sans supprimer les données :

```bash
docker compose down
```

Les données PostgreSQL et les médias résident dans les volumes Docker
`postgres_data` et `media_data`. `docker compose down -v` supprime ces volumes
et toutes les données qu'ils contiennent.

## Utiliser une base PostgreSQL externe

La configuration Django accepte également un `DATABASE_URL` fourni par un
service PostgreSQL externe. Si cette base est utilisée, adaptez le service
`web` dans `compose.yaml` et ne démarrez pas le service `db`.

## Médias dans un stockage objet

Par défaut, les médias sont persistés dans le volume `media_data`. Pour un
déploiement multi-instance ou un stockage géré, configurez les variables S3
`SUPABASE_S3_ACCESS_KEY` et `SUPABASE_S3_SECRET_KEY` (et l'endpoint/région).
Le backend objet est activé lorsque les deux clés sont présentes.
