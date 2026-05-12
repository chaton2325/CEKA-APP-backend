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

### Supprimer son compte

La suppression immediate demande le mot de passe actuel.

```http
DELETE /auth/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "password123"
}
```

### Demander la suppression de ses donnees

Cette route cree une demande `pending` a traiter cote administration/support.

```http
POST /auth/me/data-deletion-request
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "reason": "Je souhaite supprimer mes donnees"
}
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
Content-Type: multipart/form-data
```

Champs:

- `content`: texte optionnel si au moins un media est envoye
- `media`: fichiers image/audio/video, champ repetable pour envoyer plusieurs fichiers

Formats image acceptes: `jpg`, `jpeg`, `png`, `webp`.
Formats video acceptes: `mp4`, `mov`, `webm`, `mkv`.
Formats audio acceptes: `mp3`, `wav`, `ogg`, `m4a`, `aac`.

Il est possible d'envoyer plusieurs images, videos, audios, ou un melange
image/audio/video dans la meme publication.

Pour une publication texte simple, `application/json` reste accepte:

```json
{
  "content": "Ma premiere publication"
}
```

### Lister les publications

```http
GET /posts
```

Chaque post renvoie:

- `media`: liste des audios/videos attaches
- `likes_count`: nombre de likes
- `liked_by`: utilisateurs ayant like
- `comments`: commentaires racine avec auteur, likes et reponses

### Voir les publications d'un profil

```http
GET /users/<user_id>/posts
```

### Modifier / supprimer une publication

Seul l'auteur du post peut modifier ou supprimer.

```http
PUT /posts/<post_id>
PATCH /posts/<post_id>
DELETE /posts/<post_id>
Authorization: Bearer <access_token>
```

En modification, envoyer `content` en JSON ou `multipart/form-data`. Pour ajouter des
medias, envoyer `media`. Pour remplacer tous les medias existants, envoyer
`replace_media=true`.

### Liker / unliker une publication

```http
POST /posts/<post_id>/likes
DELETE /posts/<post_id>/likes
Authorization: Bearer <access_token>
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

Pour repondre a un commentaire, envoyer `parent_id`:

```json
{
  "content": "Ma reponse",
  "parent_id": 1
}
```

### Liker / unliker un commentaire

```http
POST /comments/<comment_id>/likes
DELETE /comments/<comment_id>/likes
Authorization: Bearer <access_token>
```

## Notifications

Les notifications sont creees quand un autre utilisateur commente, repond, like un
post ou like un commentaire.

```http
GET /notifications
GET /notifications?unread_only=true
PUT /notifications/<notification_id>/read
PUT /notifications/read-all
Authorization: Bearer <access_token>
```

## Recherche de profils

Recherche tolerante aux fautes simples sur le nom d'utilisateur et la bio.

```http
GET /users/search?q=alice&limit=10
```
