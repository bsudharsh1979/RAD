export function notebookHref(file?: string | null, cell?: number | null) {
  if (!file) return "/notebooks";
  const base = `/notebooks/${encodeURIComponent(file)}`;
  return cell == null ? `${base}?walkthrough=1` : `${base}?cell=${cell}&walkthrough=1`;
}

export function conceptHref(id: string) {
  return `/learn?concept=${encodeURIComponent(id)}`;
}

export function topicHref(id: string) {
  return `/learn/${encodeURIComponent(id)}`;
}

export function twinHref(id?: string | null) {
  return id ? `/twins/${id}` : "/twins";
}
