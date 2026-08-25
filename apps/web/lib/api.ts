export const API = "/api";

export async function api<T = unknown>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export type Evidence =
  | "COURSE_SOURCE"
  | "EXPECTED_RESULT"
  | "SIMULATED_RESULT"
  | "ACTUAL_RUN"
  | "TUTOR_INTERPRETATION"
  | "EXTERNAL_RESEARCH";
