# Documentation Frontend CEKA API

## Base URL

En local:

```txt
http://localhost:5000
```

Toutes les reponses sont en JSON, sauf `GET /uploads/<filename>` qui sert un fichier.

## Authentification

Les routes protegees demandent l'en-tete suivant:

```http
Authorization: Bearer <access_token>
```

Le token est renvoye par `POST /auth/register` et `POST /auth/login`.

## Configuration Backend Utile

Variables `.env` utilisees pour les codes:

```env
REGISTRATION_CODE=CEKA2026
PASSWORD_RESET_CODE_EXPIRATION_MINUTES=15
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_FROM_EMAIL=no-reply@example.com
SMTP_FROM_NAME=CEKA
SMTP_TIMEOUT_SECONDS=10
```

## Health Check

```http
GET /health
```

Reponse `200`:

```json
{
  "status": "ok"
}
```

## Inscription

```http
POST /auth/register
Content-Type: application/json
```

Body:

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "password123",
  "registration_code": "CEKA2026"
}
```

Reponse `201`:

```json
{
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "bio": null,
    "profile_photo_url": null,
    "banner_photo_url": null,
    "created_at": "2026-05-12T10:00:00",
    "updated_at": "2026-05-12T10:00:00"
  },
  "access_token": "..."
}
```

Erreurs possibles:

- `400`: `username_email_password_code_required`
- `400`: `password_min_8_chars`
- `403`: `invalid_registration_code`
- `409`: `username_or_email_already_exists`

## Connexion

```http
POST /auth/login
Content-Type: application/json
```

Body:

```json
{
  "email": "alice@example.com",
  "password": "password123"
}
```

Reponse `200`:

```json
{
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "bio": null,
    "profile_photo_url": null,
    "banner_photo_url": null,
    "created_at": "2026-05-12T10:00:00",
    "updated_at": "2026-05-12T10:00:00"
  },
  "access_token": "..."
}
```

Erreurs possibles:

- `400`: `email_password_required`
- `401`: `invalid_credentials`

## Mot De Passe Oublie

Cette route genere un code de recuperation et l'envoie par email si l'utilisateur
existe.

```http
POST /auth/password/forgot
Content-Type: application/json
```

Body:

```json
{
  "email": "alice@example.com"
}
```

Reponse `200`:

```json
{
  "message": "password_reset_code_sent"
}
```

Si l'email n'existe pas, la route renvoie quand meme `200`:

```json
{
  "message": "password_reset_code_sent"
}
```

Erreurs possibles:

- `400`: `email_required`
- `502`: `password_reset_email_failed`
- `503`: `smtp_host_required`
- `503`: `smtp_from_email_required`

## Reinitialiser Le Mot De Passe

```http
POST /auth/password/reset
Content-Type: application/json
```

Body:

```json
{
  "email": "alice@example.com",
  "code": "123456",
  "new_password": "newpassword123"
}
```

Reponse `200`:

```json
{
  "message": "password_reset_success"
}
```

Erreurs possibles:

- `400`: `email_code_new_password_required`
- `400`: `password_min_8_chars`
- `400`: `invalid_or_expired_reset_code`

## Changer Son Mot De Passe

Route protegee pour un utilisateur deja connecte.

```http
PUT /auth/me/password
Authorization: Bearer <access_token>
Content-Type: application/json
```

Body:

```json
{
  "current_password": "password123",
  "new_password": "newpassword123"
}
```

Reponse `200`:

```json
{
  "message": "password_changed"
}
```

Erreurs possibles:

- `400`: `current_password_new_password_required`
- `400`: `password_min_8_chars`
- `401`: `missing_bearer_token`
- `401`: `invalid_token`
- `401`: `invalid_current_password`

## Utilisateur Connecte

```http
GET /auth/me
Authorization: Bearer <access_token>
```

Reponse `200`:

```json
{
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "bio": null,
    "profile_photo_url": null,
    "banner_photo_url": null,
    "created_at": "2026-05-12T10:00:00",
    "updated_at": "2026-05-12T10:00:00"
  }
}
```

Erreurs possibles:

- `401`: `missing_bearer_token`
- `401`: `invalid_token`
- `401`: `user_not_found`

## Consulter Un Profil Public

Par ID:

```http
GET /users/<user_id>
```

Par nom d'utilisateur:

```http
GET /users/by-username/<username>
```

Reponse `200`:

```json
{
  "user": {
    "id": 1,
    "username": "alice",
    "bio": "Ma bio",
    "profile_photo_url": "/uploads/profile-photos/image.png",
    "banner_photo_url": "/uploads/banners/image.png",
    "created_at": "2026-05-12T10:00:00",
    "updated_at": "2026-05-12T10:05:00"
  }
}
```

Le profil public ne renvoie pas l'email de l'utilisateur.

Erreurs possibles:

- `404`: `user_not_found`

## Modifier Le Profil

```http
PUT /auth/me/profile
Authorization: Bearer <access_token>
Content-Type: application/json
```

Body JSON:

```json
{
  "username": "alice2",
  "bio": "Ma bio"
}
```

Pour envoyer des images, utiliser `multipart/form-data`:

```txt
username: alice2
bio: Ma bio
profile_photo: fichier image
banner_photo: fichier image
```

Formats image acceptes:

- `jpg`
- `jpeg`
- `png`
- `webp`

Reponse `200`:

```json
{
  "user": {
    "id": 1,
    "username": "alice2",
    "email": "alice@example.com",
    "bio": "Ma bio",
    "profile_photo_url": "/uploads/profile-photos/image.png",
    "banner_photo_url": "/uploads/banners/image.png",
    "created_at": "2026-05-12T10:00:00",
    "updated_at": "2026-05-12T10:05:00"
  }
}
```

Erreurs possibles:

- `400`: `invalid_image_type`
- `409`: `username_already_exists`

## Lister Les Posts

```http
GET /posts
```

Reponse `200`:

```json
{
  "posts": [
    {
      "id": 1,
      "content": "Ma premiere publication",
      "author": {
        "id": 1,
        "username": "alice",
        "profile_photo_url": null
      },
      "media": [
        {
          "id": 1,
          "url": "/uploads/posts/photo.jpg",
          "media_type": "image",
          "filename": "photo.jpg",
          "position": 0
        },
        {
          "id": 2,
          "url": "/uploads/posts/video.mp4",
          "media_type": "video",
          "filename": "video.mp4",
          "position": 1
        },
        {
          "id": 3,
          "url": "/uploads/posts/audio.mp3",
          "media_type": "audio",
          "filename": "audio.mp3",
          "position": 2
        }
      ],
      "likes_count": 1,
      "liked_by": [
        {
          "id": 2,
          "username": "bob",
          "profile_photo_url": null
        }
      ],
      "comments": [
        {
          "id": 1,
          "content": "Mon commentaire",
          "author": {
            "id": 2,
            "username": "bob",
            "profile_photo_url": null
          },
          "post_id": 1,
          "parent_id": null,
          "likes_count": 0,
          "liked_by": [],
          "replies": [],
          "created_at": "2026-05-12T10:02:00",
          "updated_at": "2026-05-12T10:02:00"
        }
      ],
      "created_at": "2026-05-12T10:00:00",
      "updated_at": "2026-05-12T10:00:00"
    }
  ]
}
```

## Creer Un Post

```http
POST /posts
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

Champs `multipart/form-data`:

- `content`: texte optionnel si au moins un media est envoye
- `media`: fichier image/audio/video, champ repetable pour plusieurs fichiers

Formats acceptes:

- Image: `jpg`, `jpeg`, `png`, `webp`
- Video: `mp4`, `mov`, `webm`, `mkv`
- Audio: `mp3`, `wav`, `ogg`, `m4a`, `aac`

Exemple:

```txt
content: Ma publication avec plusieurs medias
media: photo.jpg
media: intro.mp4
media: vocal.mp3
```

Pour un post texte seul, `application/json` reste accepte:

```json
{
  "content": "Ma premiere publication"
}
```

Reponse `201`:

```json
{
  "post": {
    "id": 1,
    "content": "Ma premiere publication",
    "author": {
      "id": 1,
      "username": "alice",
      "profile_photo_url": null
    },
    "media": [],
    "likes_count": 0,
    "liked_by": [],
    "comments": [],
    "created_at": "2026-05-12T10:00:00",
    "updated_at": "2026-05-12T10:00:00"
  }
}
```

Erreurs possibles:

- `400`: `content_or_media_required`
- `400`: `invalid_media_type`
- `401`: `missing_bearer_token`
- `401`: `invalid_token`

## Voir Un Post

```http
GET /posts/<post_id>
```

Reponse `200`:

```json
{
  "post": {
    "id": 1,
    "content": "Ma premiere publication",
    "author": {
      "id": 1,
      "username": "alice",
      "profile_photo_url": null
    },
    "media": [],
    "likes_count": 0,
    "liked_by": [],
    "comments": [],
    "created_at": "2026-05-12T10:00:00",
    "updated_at": "2026-05-12T10:00:00"
  }
}
```

Erreurs possibles:

- `404`: `post_not_found`

## Liker Un Post

```http
POST /posts/<post_id>/likes
Authorization: Bearer <access_token>
```

Reponse `200`:

```json
{
  "post": {
    "id": 1,
    "content": "Ma premiere publication",
    "author": {
      "id": 1,
      "username": "alice",
      "profile_photo_url": null
    },
    "media": [],
    "likes_count": 1,
    "liked_by": [
      {
        "id": 2,
        "username": "bob",
        "profile_photo_url": null
      }
    ],
    "comments": [],
    "created_at": "2026-05-12T10:00:00",
    "updated_at": "2026-05-12T10:00:00"
  }
}
```

Erreurs possibles:

- `401`: `missing_bearer_token`
- `401`: `invalid_token`
- `404`: `post_not_found`

## Retirer Son Like D'un Post

```http
DELETE /posts/<post_id>/likes
Authorization: Bearer <access_token>
```

Reponse `200`: meme format que `POST /posts/<post_id>/likes`.

Erreurs possibles:

- `401`: `missing_bearer_token`
- `401`: `invalid_token`
- `404`: `post_not_found`

## Commenter Un Post

```http
POST /posts/<post_id>/comments
Authorization: Bearer <access_token>
Content-Type: application/json
```

Body:

```json
{
  "content": "Mon commentaire"
}
```

Pour repondre a un commentaire, ajouter `parent_id`:

```json
{
  "content": "Ma reponse",
  "parent_id": 1
}
```

Reponse `201`:

```json
{
  "comment": {
    "id": 1,
    "content": "Mon commentaire",
    "author": {
      "id": 1,
      "username": "alice",
      "profile_photo_url": null
    },
    "post_id": 1,
    "parent_id": null,
    "likes_count": 0,
    "liked_by": [],
    "replies": [],
    "created_at": "2026-05-12T10:00:00",
    "updated_at": "2026-05-12T10:00:00"
  }
}
```

Erreurs possibles:

- `400`: `content_required`
- `400`: `invalid_parent_id`
- `401`: `missing_bearer_token`
- `401`: `invalid_token`
- `404`: `post_not_found`
- `404`: `comment_not_found`

## Liker Un Commentaire

```http
POST /comments/<comment_id>/likes
Authorization: Bearer <access_token>
```

Reponse `200`:

```json
{
  "message": "comment_liked"
}
```

Erreurs possibles:

- `401`: `missing_bearer_token`
- `401`: `invalid_token`
- `404`: `comment_not_found`

## Retirer Son Like D'un Commentaire

```http
DELETE /comments/<comment_id>/likes
Authorization: Bearer <access_token>
```

Reponse `200`:

```json
{
  "message": "comment_unliked"
}
```

Erreurs possibles:

- `401`: `missing_bearer_token`
- `401`: `invalid_token`
- `404`: `comment_not_found`

## Afficher Une Image Uploadee

```http
GET /uploads/<filename>
```

Exemple:

```txt
http://localhost:5000/uploads/profile-photos/image.png
```

Les champs `profile_photo_url` et `banner_photo_url` peuvent etre utilises comme chemins d'image. Cote frontend, prefixer avec la Base URL si le chemin commence par `/uploads`.
