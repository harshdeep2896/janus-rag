class IngestionError(Exception):
    """Base for ingestion failures that retrying cannot fix."""


class UnsupportedMimeTypeError(IngestionError):
    """File type is not supported (e.g. PDF for now)."""


class DocumentParseError(IngestionError):
    """File bytes could not be turned into text (e.g. not valid UTF-8)."""


class EmptyDocumentError(IngestionError):
    """File was parsed but produced no text to chunk."""