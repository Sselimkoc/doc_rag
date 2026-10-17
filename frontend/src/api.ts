export type Document = {
  id: number
  filename: string
  content_type: string
  size: number
  status: string
  created_at: string
  page_count: number
  ocr_page_count: number
}

export async function listDocuments(
  query: { offset: number; limit: number } | { ids: number[] },
): Promise<Document[]> {
  const params =
    'ids' in query
      ? query.ids.map((id) => `ids=${id}`).join('&')
      : `offset=${query.offset}&limit=${query.limit}`
  const res = await fetch(`/documents?${params}`)
  if (!res.ok) throw new Error('list')
  return res.json()
}

export async function uploadDocument(file: File): Promise<Document> {
  const body = new FormData()
  body.append('file', file)
  const res = await fetch('/documents', { method: 'POST', body })
  if (!res.ok) throw new Error(res.status === 415 ? 'unsupported' : 'upload')
  return res.json()
}

export type PageText = {
  page: number
  text: string
}

export async function getDocumentText(id: number): Promise<PageText[]> {
  const res = await fetch(`/documents/${id}/text`)
  if (!res.ok) throw new Error('text')
  return res.json()
}

export function documentFileUrl(id: number) {
  return `/documents/${id}/file`
}
