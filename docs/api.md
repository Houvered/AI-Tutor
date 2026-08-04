# API Reference

This page lists every endpoint the backend provides. All endpoints start with
`/api`. Requests and responses are JSON, except file upload.

The web page itself is served by the backend at the root `/` after the frontend
is built. One address serves both the UI and the API.

## Documents

### Upload a file

```
POST /api/documents/upload
Content-Type: multipart/form-data
Field name: file
```

Supported types: PDF, DOCX, PPTX, TXT, Markdown.

Response:

```json
{
  "id": "abc-123",
  "filename": "notes.pdf",
  "created_at": "2026-08-04T12:00:00"
}
```

The file is parsed, chunked, embedded, and stored before the response returns.
Large files may take a few seconds.

### List documents

```
GET /api/documents
```

Response:

```json
{
  "documents": [
    {
      "id": "abc-123",
      "filename": "notes.pdf",
      "created_at": "2026-08-04T12:00:00"
    }
  ]
}
```

### Delete a document

```
DELETE /api/documents/{id}
```

Removes the file and all its chunks.

## Ask

### Ask a question

```
POST /api/ask
{
  "message": "What is a binary search tree?",
  "history": [
    {"role": "user", "content": "previous question"},
    {"role": "assistant", "content": "previous answer"}
  ]
}
```

`history` is optional. Send the last few messages so the answer can keep context.

Response:

```json
{
  "answer": "A binary search tree is ... [1]",
  "citations": [
    {
      "index": 1,
      "text": "the matching passage",
      "filename": "notes.pdf"
    }
  ]
}
```

The answer is grounded in the user's uploaded material only. If nothing matches,
the answer says so. If the AI service is down, the answer shows the closest
material directly instead of failing.

## Quiz

### Generate quiz questions

```
POST /api/quiz/generate
{
  "question": "binary search tree",
  "count": 3
}
```

`count` is optional and defaults to 3.

The questions are generated from the user's uploaded material. The model
returns strict JSON, which is validated. If the JSON is invalid the server
retries up to 3 times, then returns a 422 error instead of crashing.

Response:

```json
{
  "questions": [
    {
      "question": "Which property holds in a binary search tree?",
      "options": ["a", "b", "c", "d"],
      "correct_index": 0,
      "explanation": "The left child holds a smaller key."
    }
  ]
}
```

### Evaluate a quiz answer

```
POST /api/quiz/evaluate
{
  "selected_index": 2,
  "correct_index": 0,
  "explanation": "The left child holds a smaller key."
}
```

Response:

```json
{
  "correct": false,
  "explanation": "The left child holds a smaller key.",
  "selected_index": 2,
  "correct_index": 0
}
```

## Review

### Get due reviews

```
GET /api/revision
```

Response:

```json
{
  "revisions": [
    {
      "topic": "Binary Search Tree",
      "ease": 2.5,
      "interval_days": 1,
      "next_review": "2026-08-05"
    }
  ]
}
```

Only topics due today or earlier are returned.

### Grade a review

```
POST /api/revision/grade
{
  "topic": "Binary Search Tree",
  "quality": 4
}
```

`quality` is from 0 to 5. 5 means the answer came easily, 0 means total failure.
The SM-2 algorithm updates the schedule.

## Health

### Check the app

```
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "llm_connected": true,
  "documents_count": 3
}
```

`llm_connected` is false if the LLM API cannot be reached or the key is wrong.

## Errors

Errors follow one shape:

```json
{
  "detail": "human readable message"
}
```

The status code tells you the kind of error:

- 400: bad request (for example unsupported file type).
- 404: not found (for example deleting an unknown document).
- 500: internal error.