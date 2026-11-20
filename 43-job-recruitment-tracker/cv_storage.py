"""
Local file storage manager and validation for applicant CV documents.
"""
import hashlib
import os
import secrets
import shutil

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 Megabytes
DEFAULT_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads", "cvs")


class CVStorageManager:
    def __init__(self, upload_dir: str = None):
        self.upload_dir = upload_dir or DEFAULT_UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    @staticmethod
    def validate_cv_file(filename: str, file_size_bytes: int):
        """Validate file extension and size boundaries."""
        if not filename or "." not in filename:
            raise ValueError("Invalid file name. File must have a valid extension.")

        ext = filename.rsplit(".", 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file format '.{ext}'. Allowed types are: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

        if file_size_bytes <= 0:
            raise ValueError("File is empty (0 bytes). Cannot upload empty CV.")

        if file_size_bytes > MAX_FILE_SIZE_BYTES:
            max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
            raise ValueError(f"File size exceeds maximum allowable limit of {max_mb:.1f} MB.")

    def save_cv_bytes(self, candidate_code: str, original_filename: str, content_bytes: bytes) -> dict:
        """Save CV document from raw bytes."""
        size = len(content_bytes)
        self.validate_cv_file(original_filename, size)

        ext = original_filename.rsplit(".", 1)[1].lower()
        sha256_hash = hashlib.sha256(content_bytes).hexdigest()

        # Unique stored filename: cv_{cand_code}_{random_hex}.{ext}
        token = secrets.token_hex(6)
        stored_filename = f"cv_{candidate_code.lower()}_{token}.{ext}"
        destination_path = os.path.join(self.upload_dir, stored_filename)

        with open(destination_path, "wb") as f:
            f.write(content_bytes)

        return {
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "file_path": destination_path,
            "file_type": ext,
            "file_size_bytes": size,
            "checksum_sha256": sha256_hash,
        }

    def save_cv_from_path(self, candidate_code: str, source_path: str) -> dict:
        """Copy CV document from an existing filesystem path."""
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found at: {source_path}")

        file_size = os.path.getsize(source_path)
        original_filename = os.path.basename(source_path)
        self.validate_cv_file(original_filename, file_size)

        with open(source_path, "rb") as f:
            content = f.read()

        return self.save_cv_bytes(candidate_code, original_filename, content)
