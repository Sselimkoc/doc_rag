import { useEffect, useRef, useState } from 'react'
import { listDocuments, uploadDocument, type Document } from './api'

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function App() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    listDocuments().then(setDocuments).catch((e) => setError(e.message))
  }, [])

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
              <strong>{doc.filename}</strong>
              <div>
                {doc.content_type} · {formatSize(doc.size)} ·{' '}
                {new Date(doc.created_at).toLocaleString('tr-TR')}
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}

export default App
