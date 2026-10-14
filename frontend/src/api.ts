export type Document = {
  id: number
  filename: string
  content_type: string
  size: number
  status: string
  created_at: string
}

export async function listDocuments(): Promise<Document[]> {
  const res = await fetch('/documents')
  if (!res.ok) throw new Error('Belgeler alınamadı.')
  return res.json()
}

export async function uploadDocument(file: File): Promise<Document> {
  const body = new FormData()
  body.append('file', file)
  const res = await fetch('/documents', { method: 'POST', body })
  if (!res.ok) {
    const data = await res.json().catch(() => null)
    throw new Error(data?.detail ?? 'Yükleme başarısız.')
  }
  return res.json()
}

export function documentFileUrl(id: number) {
  return `/documents/${id}/file`
}
