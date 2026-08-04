import React, { useEffect, useState } from "react";
import {
  api,
  AskResult,
  Citation,
  DocumentItem,
  QuizQuestion,
  RevisionItem,
} from "./api";

type Tab = "ask" | "notes" | "review";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  error?: boolean;
}

export const App: React.FC = () => {
  const [tab, setTab] = useState<Tab>("ask");
  return (
    <div className="app">
      <header className="header">
        <h1>StudyMate</h1>
        <nav className="tabs">
          <button className={tab === "ask" ? "active" : ""} onClick={() => setTab("ask")}>
            Ask
          </button>
          <button className={tab === "notes" ? "active" : ""} onClick={() => setTab("notes")}>
            Notes
          </button>
          <button className={tab === "review" ? "active" : ""} onClick={() => setTab("review")}>
            Review
          </button>
        </nav>
      </header>
      <main>
        {tab === "ask" && <AskView />}
        {tab === "notes" && <NotesView />}
        {tab === "review" && <ReviewView />}
      </main>
    </div>
  );
};

/* ---------------- Ask ---------------- */

const AskView: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [quiz, setQuiz] = useState<QuizQuestion | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [result, setResult] = useState<{ correct: boolean; explanation: string } | null>(
    null
  );

  const history = messages
    .filter((m) => m.role === "user" || (m.role === "assistant" && !m.error))
    .slice(-6)
    .map((m) => ({ role: m.role, content: m.content }));

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setQuiz(null);
    setSelected(null);
    setResult(null);
    setMessages((m) => [...m, { role: "user", content: text }]);
    setBusy(true);
    try {
      const res = await api<AskResult>("/ask", {
        method: "POST",
        body: JSON.stringify({ message: text, history }),
      });
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, citations: res.citations },
      ]);
      await loadQuiz(text);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Request failed";
      setMessages((m) => [...m, { role: "assistant", content: message, error: true }]);
    } finally {
      setBusy(false);
    }
  };

  const loadQuiz = async (topic: string) => {
    try {
      const res = await api<{ questions: QuizQuestion[] }>("/quiz/generate", {
        method: "POST",
        body: JSON.stringify({ question: topic, count: 1 }),
      });
      if (res.questions.length) setQuiz(res.questions[0]);
    } catch {
      // a quiz is optional; skip quietly if generation fails
    }
  };

  const answer = async (index: number) => {
    if (!quiz) return;
    setSelected(index);
    const res = await api<{ correct: boolean; explanation: string }>("/quiz/evaluate", {
      method: "POST",
      body: JSON.stringify({
        selected_index: index,
        correct_index: quiz.correct_index,
        explanation: quiz.explanation,
        topic: lastUserQuestion(),
      }),
    });
    setResult(res);
  };

  const lastUserQuestion = () => {
    const last = [...messages].reverse().find((m) => m.role === "user");
    return last ? last.content.slice(0, 60) : "";
  };

  return (
    <div className="ask">
      <div className="chat">
        {messages.length === 0 && (
          <p className="empty">Ask a question about your notes. Upload your material first in the Notes tab.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <p>{m.content}</p>
            {m.citations && m.citations.length > 0 && (
              <div className="citations">
                {m.citations.map((c) => (
                  <span key={c.index} title={c.text}>
                    [{c.index}] {c.filename}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {busy && <p className="msg assistant typing">Thinking...</p>}
      </div>

      {quiz && selected === null && (
        <div className="quiz">
          <h3>Check your understanding</h3>
          <p>{quiz.question}</p>
          {quiz.options.map((opt, i) => (
            <button key={i} className="option" onClick={() => answer(i)}>
              {opt}
            </button>
          ))}
        </div>
      )}

      {result && quiz && (
        <div className="quiz">
          <h3 className={result.correct ? "correct" : "wrong"}>
            {result.correct ? "Correct" : "Not quite"}
          </h3>
          {result.explanation && <p>{result.explanation}</p>}
          <button className="option" onClick={() => { setQuiz(null); setResult(null); }}>
            Next question
          </button>
        </div>
      )}

      <form
        className="composer"
        onSubmit={(e) => { e.preventDefault(); send(); }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something..."
        />
        <button type="submit" disabled={busy || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
};

/* ---------------- Notes ---------------- */

const NotesView: React.FC = () => {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const res = await api<{ documents: DocumentItem[] }>("/documents");
      setDocs(res.documents);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    load();
  }, []);

  const upload = async (file: File) => {
    setBusy(true);
    setError("");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("/api/documents/upload", { method: "POST", body: form });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || "Upload failed");
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: string) => {
    await api<{ deleted: boolean }>(`/documents/${id}`, { method: "DELETE" });
    setDocs((d) => d.filter((x) => x.id !== id));
  };

  return (
    <div className="notes">
      <label className="dropzone">
        <input
          type="file"
          accept=".pdf,.docx,.pptx,.txt,.md"
          disabled={busy}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) upload(file);
            e.target.value = "";
          }}
        />
        {busy ? "Uploading and indexing..." : "Upload a study file (PDF, DOCX, PPTX, TXT, MD)"}
      </label>
      {error && <p className="error">{error}</p>}
      <ul className="doclist">
        {docs.map((d) => (
          <li key={d.id}>
            <span className="name">{d.filename}</span>
            <span className="date">{new Date(d.created_at).toLocaleString()}</span>
            <button onClick={() => remove(d.id)}>Delete</button>
          </li>
        ))}
        {docs.length === 0 && <li className="empty-row">No documents yet.</li>}
      </ul>
    </div>
  );
};

/* ---------------- Review ---------------- */

const ReviewView: React.FC = () => {
  const [items, setItems] = useState<RevisionItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const res = await api<{ revisions: RevisionItem[] }>("/revision");
      setItems(res.revisions);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    load();
  }, []);

  const grade = async (topic: string, quality: number) => {
    setBusy(true);
    setError("");
    try {
      await api("/revision/grade", {
        method: "POST",
        body: JSON.stringify({ topic, quality }),
      });
      setItems((list) => list.filter((x) => x.topic !== topic));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Grade failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="review">
      {error && <p className="error">{error}</p>}
      {items.length === 0 ? (
        <p className="empty">Nothing due right now. Answer quiz questions correctly and review topics will appear here.</p>
      ) : (
        items.map((item) => (
          <div key={item.topic} className="card">
            <h3>{item.topic}</h3>
            <p className="meta">
              #{item.repetitions} solid · ease {item.ease} · next {item.next_review}
            </p>
            <div className="grades">
              {[0, 1, 2, 3, 4, 5].map((q) => (
                <button key={q} disabled={busy} onClick={() => grade(item.topic, q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
};