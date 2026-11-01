"""Safe parsing of uploaded email files (Member 3).

Supported uploads: ``.eml`` (one email) and ``.csv`` (many emails).

Safety rules enforced here:

* File name, extension and size are validated BEFORE any parsing.
* Attachments are only *listed* (name, type, size). They are never saved,
  opened or executed, and their contents are never returned.
* URLs inside the email stay plain text; nothing is fetched.
"""

import csv
import io
import re
from email import policy
from email.parser import BytesParser
from typing import Any

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_CSV_ROWS = 500
ALLOWED_EXTENSIONS = (".eml", ".csv")
RISKY_ATTACHMENT_EXTENSIONS = frozenset(
    {".exe", ".scr", ".bat", ".cmd", ".com", ".js", ".jse", ".vbs", ".vbe", ".ps1", ".jar", ".msi",
     ".lnk", ".iso", ".docm", ".xlsm", ".pptm", ".hta"}
)


class IngestError(ValueError):
    """Raised when an uploaded file is not acceptable."""


def validate_upload(filename: str, size: int) -> str:
    """Check an upload's name, extension and size before reading it.

    Args:
        filename: The name supplied by the uploader (a bare file name, no folders).
        size: The size in bytes.

    Returns:
        The lower-case extension (``'.eml'`` or ``'.csv'``).

    Raises:
        IngestError: If the name is unsafe, the type is not allowed, or the
            size is zero or above ``MAX_UPLOAD_BYTES``.
    """
    if not isinstance(filename, str) or not filename.strip():
        raise IngestError("Upload has no file name.")
    if any(char in filename for char in ("/", "\\", "\x00")) or ".." in filename:
        raise IngestError("Upload file name must not contain folders, '..' or null characters.")
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise IngestError(f"Unsupported file type {extension or '(none)'}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}.")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise IngestError("Upload is empty.")
    if size > MAX_UPLOAD_BYTES:
        raise IngestError(f"Upload is too large ({size} bytes). The limit is {MAX_UPLOAD_BYTES} bytes.")
    return extension


# @@PART 2
def _safe_name(name: str) -> str:
    """Make an attachment name safe to display (no folders, no control characters)."""
    base = re.split(r"[\\/]", name or "")[-1]
    return re.sub(r"[\x00-\x1f\x7f]", "", base)[:120]


def attachment_warnings(attachments: list[dict[str, Any]]) -> list[str]:
    """Return a warning for each attachment with a risky (executable/macro) extension."""
    warnings = []
    for item in attachments:
        name = item.get("filename", "")
        extension = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if extension in RISKY_ATTACHMENT_EXTENSIONS:
            warnings.append(
                f"Attachment '{name}' has a potentially executable or macro-enabled type ({extension}). Do not open it."
            )
    return warnings


def parse_eml(data: bytes) -> dict[str, Any]:
    """Parse one ``.eml`` file.

    Args:
        data: The raw bytes of the file (already size-checked).

    Returns:
        A dict with ``subject``, ``body`` (plain text, or HTML source if there
        is no plain part), ``sender``, ``attachments`` (list of dicts with
        ``filename``, ``content_type``, ``size``) and ``attachment_warnings``.

    Raises:
        IngestError: If the data is not bytes, is too large, or cannot be parsed.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise IngestError("EML data must be bytes.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise IngestError("EML data is too large.")
    try:
        message = BytesParser(policy=policy.default).parsebytes(bytes(data))
        body_part = message.get_body(preferencelist=("plain", "html"))
        body = body_part.get_content() if body_part is not None else ""
        attachments = [
            {
                "filename": _safe_name(part.get_filename() or ""),
                "content_type": part.get_content_type(),
                "size": len(part.get_payload(decode=True) or b""),
            }
            for part in message.iter_attachments()
        ]
        subject = str(message["subject"] or "")
        sender = str(message["from"] or "")
    except (LookupError, UnicodeError, ValueError, AttributeError) as error:
        raise IngestError(f"Could not parse the .eml file: {error}") from error
    return {
        "subject": subject,
        "body": body,
        "sender": sender,
        "attachments": attachments,
        "attachment_warnings": attachment_warnings(attachments),
    }


# @@PART 3
def parse_csv_upload(data: bytes) -> list[dict[str, str]]:
    """Parse an uploaded ``.csv`` of emails.

    The header row must contain a ``subject`` and/or ``body`` column (any
    capitalization); ``sender`` is optional. A ``label`` column is ignored.

    Returns:
        A list of dicts with ``subject``, ``body`` and ``sender`` strings.

    Raises:
        IngestError: If the data is not UTF-8 text, has no usable header or
            rows, or has more than ``MAX_CSV_ROWS`` rows.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise IngestError("CSV data must be bytes.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise IngestError("CSV data is too large.")
    try:
        text = bytes(data).decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise IngestError("CSV must be UTF-8 text.") from error
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        header = {(name or "").strip().lower(): name for name in (reader.fieldnames or [])}
        if "subject" not in header and "body" not in header:
            raise IngestError("CSV needs a 'subject' and/or 'body' column in its header row.")
        rows: list[dict[str, str]] = []
        for row in reader:
            if len(rows) >= MAX_CSV_ROWS:
                raise IngestError(f"CSV has more than {MAX_CSV_ROWS} rows.")
            rows.append(
                {field: str(row.get(header[field]) or "") if field in header else "" for field in ("subject", "body", "sender")}
            )
    except csv.Error as error:
        raise IngestError(f"Could not parse the CSV: {error}") from error
    if not rows:
        raise IngestError("CSV has a header but no rows.")
    return rows
