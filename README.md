# StudyMate

> Ask questions, get answers from YOUR notes, quiz yourself, and remember more.
> Your personal study companion, built around your own material.

StudyMate is a study companion that learns your notes and teaches you from them.
Upload your PDFs, slides, and documents. Ask questions in plain language. StudyMate
answers only from your own material, with citations you can check. Then it quizzes
you and schedules reviews so you never forget.

## Why you will love it

- Answers that you can trust. Every answer comes from your uploaded material,
  never from random internet knowledge. Every answer shows citations you can click.
- Quiz yourself without writing questions. StudyMate builds a mini quiz from your
  own material after every answer.
- Remember what you learn. Spaced repetition (the SM-2 method) schedules the right
  topic for review at the right time.
- Runs anywhere. One server, one file for your data, one small app. No Docker, no
  database server, no GPU, no local AI models.
- Your data stays yours. Everything is stored in one local SQLite file. Nothing is
  sent anywhere except the questions you ask, to the AI provider you choose.

## What you can do

| Feature | What it does |
| --- | --- |
| Notes | Upload PDF, DOCX, PPTX, TXT, or Markdown study material. |
| Ask | Ask questions and get grounded answers with citations. |
| Quiz | Answer a mini quiz after every answer, built from your notes. |
| Review | See topics that are due for review today, rate your recall, keep the streak. |

## How it works

1. You upload your study material.
2. StudyMate reads it, splits it into chunks, and indexes it.
3. You ask a question. StudyMate finds the best matching parts of your notes.
4. An AI model writes an answer using only those parts, with citations.
5. StudyMate gives you a practice question and schedules the topic for review.

## Quick start

You need Python 3.11+, Node.js 18+, and an LLM API key: any OpenAI-compatible
provider (OpenAI, DeepSeek, Groq, OpenRouter, and more) or Google Gemini.

```
pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..
uvicorn backend.main:app --port 8000
```

Then open http://localhost:8000

Set your API keys in a `.env` file first. See `docs/setup.md` for the full
guide, including both provider options.

## Project structure

```
backend/    FastAPI server, all logic, serves the frontend too.
frontend/   React web app (Notes, Ask, Review).
docs/       Setup, architecture, API reference, decisions, deployment.
tests/      pytest suite for the core logic.
```

## Documentatio

- Setup and run: `docs/setup.md`
- Architecture: `docs/architecture.md`
- API reference: `docs/api.md`
- Development guide: `docs/development.md`
- Design decisions: `docs/decisions.md`
- Deployment: `docs/deployment.md`

## License

Private project. All rights reserved.
