/*
 * Update the status of a document.
 */

UPDATE documents
SET status = %(status)s,
    error = %(error)s,
    updated_at = now()
WHERE id = %(document_id)s