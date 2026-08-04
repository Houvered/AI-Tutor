// Small wrapper around fetch for the StudyMate API.

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // keep the status text
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export interface DocumentItem {
  id: string;
  filename: string;
  created_at: string;
}

export interface Citation {
  index: number;
  text: string;
  filename: string;
}

export interface AskResult {
  answer: string;
  citations: Citation[];
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface RevisionItem {
  topic: string;
  ease: number;
  interval_days: number;
  repetitions: number;
  next_review: string;
}

export interface UploadResponse {
  id: string;
  filename: string;
  created_at: string;
}
