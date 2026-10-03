from app.ingestion.errors import DocumentParseError, UnsupportedMimeTypeError


SUPPORTED_MIME_TYPES: frozenset[str] = frozenset({"text/plain", "text/markdown"})


def parse_document(data: bytes, mime_type: str) -> str:
    if mime_type not in SUPPORTED_MIME_TYPES:
        raise UnsupportedMimeTypeError(f"unsupported mime_type: {mime_type}")

    try:
        # utf-8-sig handles files that may start with a UTF-8 BOM.
        # Example: b"\xef\xbb\xbfHello" -> "Hello"
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise DocumentParseError("file is not valid UTF-8") from e
    text = text.replace("\r\n", "\n").replace(
        "\r", "\n"
    )  # Normalize line endings to LF
    return text
