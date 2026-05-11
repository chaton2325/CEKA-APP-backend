from pathlib import Path
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from config import Config


def ensure_upload_directories() -> None:
    root = Path(Config.UPLOAD_FOLDER)
    root.mkdir(parents=True, exist_ok=True)

    for directory in Config.UPLOAD_DIRECTORIES.values():
        (root / directory).mkdir(parents=True, exist_ok=True)


def save_image(file: FileStorage | None, folder_name: str) -> str | None:
    if not file or not file.filename:
        return None

    extension = file.filename.rsplit(".", 1)[-1].lower()
    if extension not in Config.ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("invalid_image_type")

    upload_dir = Path(Config.UPLOAD_FOLDER) / folder_name
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = secure_filename(file.filename)
    filename = f"{uuid4().hex}_{safe_name}"
    file.save(upload_dir / filename)

    return f"/uploads/{folder_name}/{filename}"
