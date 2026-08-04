# Setup and Run Guide

How to get this project running on your machine. Follow the steps in order.

## What you need

- Python 3.11 or newer.
- Node.js 18 or newer (only needed to build the frontend once).
- An LLM API key from one of these options:
  - Any OpenAI-compatible provider (OpenAI, DeepSeek, Groq, OpenRouter, Together AI).
  - Google Gemini (key from Google AI Studio).

No other services are needed. No Docker, no Postgres, no Redis, no local model.

## Step 1: Set environment variables

Copy the example file and fill in your values.

Create a file named `.env` in the project root. Use `.env.example` as a template.

The `.env` file has two sets of keys: one for OpenAI-compatible providers and
one for Gemini. Set which one you use with `LLM_PROVIDER`.

### Option A: OpenAI-compatible provider

```
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-secret-key-here
LLM_MODEL=gpt-4o-mini
EMBED_MODEL=text-embedding-3-small
```

Explanation:

- `LLM_BASE_URL` - the base address of your provider.
- `LLM_API_KEY` - your secret key from the provider.
- `LLM_MODEL` - the model used for chat answers and quiz questions.
- `EMBED_MODEL` - the model used to turn text into numbers for search.

If you use a different provider, change the base URL and model names. For
for example for DeepSeek the base URL is `https://api.deepseek.com/v1` and the
model is `deepseek-chat`.

### Option B: Google Gemini

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key-here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_EMBED_MODEL=gemini-embedding-001
```

Get the Gemini key from Google AI Studio: https://aistudio.google.com.

## Step 2: Install the backend

Open a terminal in the project root.

Create a virtual environment:

```
python -m venv .venv
```

Activate it:

- Windows: `.venv\Scripts\activate`
- Mac or Linux: `source .venv/bin/activate`

Install the packages:

```
pip install -r backend/requirements.txt
```

## Step 3: Build the frontend

This step creates the web page files that the backend will serve.

```
cd frontend
npm install
npm run build
cd ..
```

You only need to do this once, or again when the frontend code changes.

## Step 4: Run the app

```
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open a browser and go to:

```
http://localhost:8000
```

You should see the app. The same address serves both the web page and the API.

## Step 5: Check everything works

Open the Notes tab and upload a study file (PDF, DOCX, PPTX, TXT, or Markdown).

Then open the Ask tab and type a question about the file. You should get an answer
with citations from your own material.

## Deploying (when you want it online)

The project runs as one normal Python process. To put it online:

- Push the code to a server (any small virtual private server works).
- Repeat steps 1 to 4 on the server.
- Put nginx in front of the app if you want a public domain and HTTPS.

See `docs/development.md` for tips on running during development.