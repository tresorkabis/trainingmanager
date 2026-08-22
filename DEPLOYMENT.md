# Déploiement sur Vercel avec Supabase

Guide pour déployer **Training Manager** (Django) sur **Vercel** en utilisant
**Supabase** pour la base de données PostgreSQL **et** le stockage des fichiers
médias (photos, bordereaux, PV du jury).

---

## 1. Créer le projet Supabase

1. Créez un projet sur <https://supabase.com> (notez le **Project Ref**, ex.
   `abcdefghijklmnopqrst`).
2. **Base de données** : allez dans *Project Settings → Database → Connection
   string* et copiez la chaîne **Transaction mode pooler** (port `6543`,
   host `aws-<region>.pooler.supabase.com`). Elle ressemble à :
   ```
   postgresql://postgres.f3ab8cd...:<MOT_DE_PASSE>@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
   ```
   > Le mode *Transaction pooler* est celui recommandé par Supabase pour les
   > environnements serverless (comme Vercel) : connexions courtes et éphémères.

3. **Stockage** (pour les fichiers uploadés) :
   - Dans *Storage*, créez un bucket public nommé `media` (*Settings → Storage →
     Buckets → New bucket → public*).
   - Dans *Project Settings → Storage → S3 Access Keys*, générez une paire
     **Access Key / Secret Key** et notez la **région** du projet.

## 2. Créer le projet Vercel

1. Dans <https://vercel.com>, importez le dépôt Git du projet.
2. Framework preset : **Other** (la détection Django est automatique grâce à
   `vercel.json`).

### Variables d'environnement (Settings → Environment Variables)

| Variable              | Valeur |
|-----------------------|--------|
| `DJANGO_SECRET_KEY`   | Générer : `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG`        | `False` |
| `ALLOWED_HOSTS`       | `trainingmanager-seven.vercel.app,votre-domaine.com` |
| `CSRF_TRUSTED_ORIGINS`| `https://trainingmanager-seven.vercel.app,https://votre-domaine.com` |
| `DATABASE_URL`        | Chaîne **Transaction pooler** de Supabase |
| `SUPABASE_PROJECT_REF`| `fabcdefghijklmnopqrst` |
| `SUPABASE_S3_ACCESS_KEY` | Clé S3 générée dans Supabase |
| `SUPABASE_S3_SECRET_KEY` | Clé secrète S3 générée dans Supabase |
| `SUPABASE_S3_REGION`  | Région du projet, ex. `eu-central-1` |
| `SUPABASE_S3_BUCKET`  | `media` |

(Le fichier `.env.example` regroupe ces variables.)

## 3. Appliquer les migrations (une seule fois)

Depuis votre machine, connectez-vous à la base Supabase en utilisant la
chaîne **directe** (port `5432`) qui permet les migrations :

```bash
export DJANGO_SETTINGS_MODULE=settings.prod
export DJANGO_SECRET_KEY="votre-clé"
export DATABASE_URL="postgresql://postgres.<ref>:<mdp>@db.<ref>.supabase.co:5432/postgres"
python manage.py migrate
```

> La connexion directe à Supabase nécessite IPv6 (activé par défaut chez la
> plupart des FAI/box) ou l'add-on IPv4 payant.

Puis créer le superutilisateur admin :

```bash
python manage.py createsuperuser
```

## 4. Déployer

Poussez vos changements sur la branche liée à Vercel. Le fichier `vercel.json`
configure automatiquement :

- **Install** : `pip install -r requirements.txt`
- **Build**  : `python manage.py collectstatic --noinput`
- **Runtime** : `@vercel/python` sur `config/wsgi.py` (Python 3.12 via `.python-version`)

Vérifiez dans les logs de déploiement que `collectstatic` se termine sans
erreur (WhiteNoise est volontairement configuré sans post-processing pour
cela).

## 5. Migrer les données locales (SQLite → Supabase) — optionnel

À partir d'un dump Django du fichier `db.sqlite3` de développement :

```bash
# 1. Depuis SQLite : extraire les données
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes \
    -e auth.Permission -e admin.logentry -o data.json

# 2. Vers la base Supabase (même commande de migration que ci-dessus)
export DJANGO_SETTINGS_MODULE=settings.prod
export DJANGO_SECRET_KEY="..."
export DATABASE_URL="postgresql://postgres.<ref>:<mdp>@db.<ref>.supabase.co:5432/postgres"
python manage.py loaddata data.json
```

---

## Points d'attention

- **PDF (PV du jury)** : la génération utilise **xhtml2pdf** (pur-Python),
  compatible serverless. WeasyPrint a été retiré car il nécessite les
  bibliothèques système Pango/Cairo absentes du runtime Vercel.
- **Médias** : les fichiers uploadés sont stockés dans le bucket `media` de
  Supabase Storage (URL publique de la forme
  `https://<ref>.supabase.co/storage/v1/object/public/media/...`).
- **Migrations au déploiement** : il est préférable de ne **pas** exécuter
  `migrate` dans le build Vercel (plusieurs fonctions serverless peuvent
  s'exécuter en parallèle). Les migrations se font manuellement (section 3).
- **WeasyPrint / environment local macOS** : le chemin `DYLD_LIBRARY_PATH`
  dans `settings/base.py` est désormais inutile mais inoffensif.

## Dépannage

| Problème                            | Cause probable                                   | Solution                                                     |
|-------------------------------------|--------------------------------------------------|--------------------------------------------------------------|
| `DJANGO_SECRET_KEY` manquant        | Variable non définie dans Vercel                | L'ajouter dans Settings → Environment Variables puis redéployer |
| `DATABASE_URL` manquante            | Variable non définie                            | L'ajouter (chaîne Supabase) puis redéployer                   |
| `OperationalError: connection refused` | Mauvais mode / port pooler                  | Utiliser l'URL *Transaction* (port 6543) |
| `Permission denied` sur Upload média | Clés S3 erronées ou bucket absent               | Vérifier les clés *S3 Access Keys* et le bucket `media` public |
| Le build échoue sur `collectstatic` | Post-processing WhiteNoise activé               | Vérifier que `STATICFILES_STORAGE = None` dans `settings/prod.py` |

---

Voir aussi `config/wsgi.py` (point d'entrée WSGI) et `settings/prod.py`
(configuration réelle de production).