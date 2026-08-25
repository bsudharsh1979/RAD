export function notebookHref(file?: string | null, cell?: number | null) {
  if (!file) return "/notebooks";
  const base = `/notebooks/${encodeURIComponent(file)}`;
  return cell == null ? base : `${base}?cell=${cell}`;
}

export function conceptHref(id: string) {
  return `/learn?concept=${encodeURIComponent(id)}`;
}
