from pathlib import Path
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import secrets
from typing import Union

# Directory where uploaded input files are stored (relative to project root)
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input-files"

# Allowed extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class UploadError(Exception):
    """Generic upload error for caller to catch and handle."""
    pass


def _ensure_input_dir() -> None:
    """Create input directory if it doesn't exist."""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)


def _allowed_extension(filename: str) -> bool:
    """Return True if the filename has an allowed extension."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def _generate_token(nbytes: int = 8) -> str:
    """Generate a short URL-safe token."""
    # token_urlsafe with ~nbytes*4/3 chars, 8 bytes => ~11 chars
    return secrets.token_urlsafe(nbytes)


def save_upload(file: Union[FileStorage, object], user_id: Union[int, str]) -> str:
    """
    Save an uploaded file in the `core/input-files/` directory, renaming it to
    {user_id}_{token}.{ext}.

    Parameters
    ----------
    file : werkzeug.datastructures.FileStorage
        The uploaded file object from Flask `request.files['...']`.
    user_id : int | str
        The id of the current user (used in filename).

    Returns
    -------
    str
        The new filename (e.g. "42_Lk3j8K_a7.pdf") saved inside input-files/

    Raises
    ------
    UploadError
        If the file is invalid or saving failed.
    """
    if file is None:
        raise UploadError("No file provided.")

    # Ensure we have a FileStorage-like object with filename attribute and save() method.
    if not hasattr(file, "filename") or not hasattr(file, "save"):
        raise UploadError("Invalid file object.")

    original_filename = file.filename or ""
    if original_filename == "":
        raise UploadError("Empty filename.")

    if not _allowed_extension(original_filename):
        raise UploadError("Extension not allowed. Only PDF and DOCX are accepted.")

    # sanitize extension & filename
    secure_name = secure_filename(original_filename)
    ext = Path(secure_name).suffix.lower()

    # Build new filename
    token = _generate_token()
    new_filename = f"{user_id}_{token}{ext}"

    # Ensure directory exists
    _ensure_input_dir()

    target_path = INPUT_DIR / new_filename

    try:
        # Save file (FileStorage.save handles streaming)
        file.save(str(target_path))
    except Exception as e:
        raise UploadError(f"Failed to save uploaded file: {e}") from e

    return new_filename