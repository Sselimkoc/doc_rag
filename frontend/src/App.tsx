import { useEffect, useRef, useState } from 'react'
import {
  documentFileUrl,
  getDocumentText,
  listDocuments,
  uploadDocument,
  type Document,
  type PageText,
} from './api'

const STATUS_LABELS: Record<string, string> = {
  uploaded: 'Sırada',
  processing: 'İşleniyor',
  ready: 'Hazır',
  failed: 'Metin çıkarılamadı',
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function isPending(doc: Document) {
  return doc.status === 'uploaded' || doc.status === 'processing'
}

function App() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [pages, setPages] = useState<PageText[] | null>(null)
  const [textError, setTextError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const selected = documents.find((d) => d.id === selectedId) ?? null
  const hasPending = documents.some(isPending)

  useEffect(() => {
    listDocuments().then(setDocuments).catch((e) => setError(e.message))
  }, [])

  // İşlenen belge varken durumlar 2 saniyede bir yenilenir.
  useEffect(() => {
    if (!hasPending) return
    const timer = setInterval(() => {
      listDocuments().then(setDocuments).catch((e) => setError(e.message))
    }, 2000)
    return () => clearInterval(timer)
  }, [hasPending])

  // Seçili belge hazır olunca metni getirilir.
  useEffect(() => {
    setPages(null)
    setTextError(null)
    if (selectedId === null || selected?.status !== 'ready') return
    getDocumentText(selectedId)
      .then(setPages)
      .catch((e) => setTextError(e.message))
  }, [selectedId, selected?.status])

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return

    setUploading(true)
    setError(null)
    try {
      const doc = await uploadDocument(file)
      setDocuments((docs) => [doc, ...docs])
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <main>
      <h1>Belgeler</h1>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        onChange={handleFile}
        hidden
      />
      <button onClick={() => inputRef.current?.click()} disabled={uploading}>
        {uploading ? 'Yükleniyor…' : '+ Ekle'}
      </button>

      {error && <p role="alert">{error}</p>}

      {documents.length === 0 ? (
        <p>Henüz belge yok.</p>
      ) : (
        <ul>
          {documents.map((doc) => (
            <li key={doc.id}>
              <button
                onClick={() => setSelectedId(doc.id)}
                aria-pressed={selectedId === doc.id}
              >
                <strong>{doc.filename}</strong>
              </button>
              <div>
                {doc.content_type} · {formatSize(doc.size)} ·{' '}
                {new Date(doc.created_at).toLocaleString('tr-TR')} ·{' '}
                {STATUS_LABELS[doc.status] ?? doc.status}
              </div>
            </li>
          ))}
        </ul>
      )}

      {selected && (
        <section>
          <h2>{selected.filename}</h2>
          {selected.content_type === 'application/pdf' ? (
            <iframe
              src={documentFileUrl(selected.id)}
              title={selected.filename}
              width="100%"
              height="800"
            />
          ) : (
            <img
              src={documentFileUrl(selected.id)}
              alt={selected.filename}
              style={{ maxWidth: '100%' }}
            />
          )}

          <h3>Çıkarılan metin</h3>
          {isPending(selected) && <p>Metin çıkarılıyor…</p>}
          {selected.status === 'failed' && (
            <p role="alert">Metin çıkarılamadı. Sunucu loguna bakın.</p>
          )}
          {textError && <p role="alert">{textError}</p>}
          {pages?.map((p) => (
            <article key={p.page}>
              <h4>
                Sayfa {p.page} · {p.text.length} karakter
              </h4>
              <pre style={{ whiteSpace: 'pre-wrap' }}>
                {p.text || '(Bu sayfadan metin çıkmadı.)'}
              </pre>
            </article>
          ))}
        </section>
      )}
    </main>
  )
}

export default App
