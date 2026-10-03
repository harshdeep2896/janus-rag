/*
 * Get the content hash, filename, and mime type of a document.
 */

SELECT content_hash, filename, mime_type
FROM documents
WHERE id = %(document_id)s