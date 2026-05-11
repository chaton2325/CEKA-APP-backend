# CEKA APP Backend

Backend Python organise en MVC avec Flask et SQLAlchemy.

## Structure

- `app.py`: point d'entree de l'application.
- `controllers/`: routes et logique HTTP.
- `models/`: modeles SQLAlchemy.
- `database/`: configuration du moteur, sessions et initialisation DB.
- `config.py`: configuration chargee depuis `.env`.

## Demarrage

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Au demarrage, `init_database()` charge les modeles puis execute:

```python
Base.metadata.create_all(bind=engine)
```

Cela cree les tables manquantes dans la base configuree par `DATABASE_URL`.

## Ajouter un modele

1. Creer un fichier dans `models/`, par exemple `models/product.py`.
2. Declarer une classe qui herite de `Base`.
3. Importer ce modele dans `load_models()` dans `models/__init__.py`.

Les nouvelles tables seront creees au prochain demarrage de l'application.

## Tester la base de donnees

Le script `test_database.py` lit `DATABASE_URL` dans `.env`, tente une connexion,
charge les modeles SQLAlchemy, cree les tables manquantes, puis affiche les tables
detectees.

```bash
python test_database.py
```

## Uploads sur VPS

Par defaut, les fichiers utilisateurs sont ranges dans `uploads/`.
Au demarrage, l'application cree automatiquement:

- `uploads/profile-photos/`
- `uploads/banners/`
- `uploads/posts/`

Pour changer le dossier racine sur un VPS:

```env
UPLOAD_FOLDER=/var/www/ceka/uploads
```

## Authentification JWT

### Inscription

```http
POST /auth/register
Content-Type: application/json

{
  "username": "alice",
  "email": "alice@example.com",
  "password": "password123"
}
```

### Connexion

```http
POST /auth/login
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "password123"
}
```

Les deux routes renvoient `access_token`. Pour les routes protegees:

```http
Authorization: Bearer <access_token>
```

### Profil connecte

```http
GET /auth/me
```

### Modifier profil, photo et banniere

Envoyer en `multipart/form-data`:

- `username`: optionnel
- `bio`: optionnel
- `profile_photo`: fichier optionnel
- `banner_photo`: fichier optionnel

```http
PUT /auth/me/profile
Authorization: Bearer <access_token>
```

## Publications et commentaires

### Publier

```http
POST /posts
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "content": "Ma premiere publication"
}
```

### Lister les publications

```http
GET /posts
```

### Commenter

```http
POST /posts/<post_id>/comments
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "content": "Mon commentaire"
}
```
