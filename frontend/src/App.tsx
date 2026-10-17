import { useEffect, useRef, useState } from 'react'
import {
  documentFileUrl,
  getDocumentText,
  listDocuments,
  uploadDocument,
  type Document,
  type PageText,
} from './api'
import { initialLang, messages, saveLang, type Lang, type Messages } from './i18n'

const PAGE_SIZE = 100

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function isPending(doc: Document) {
  return doc.status === 'uploaded' || doc.status === 'processing'
}

function ocrNote(doc: Document, t: Messages) {
  if (doc.ocr_page_count === 0) return null
  if (doc.ocr_page_count === doc.page_count) return t.ocrAll
  return t.ocrSome(doc.ocr_page_count, doc.page_count)
}

function DocItem({
  doc,
  t,
  checked,
  selected,
  onCheck,
  onSelect,
}: {
  doc: Document
  t: Messages
  checked: boolean
  selected: boolean
  onCheck: () => void
  onSelect: () => void
}) {
  const note = ocrNote(doc, t)
  return (
    <li className={selected ? 'doc selected' : 'doc'}>
      <input
        type="checkbox"
        checked={checked}
        disabled={doc.status !== 'ready'}
        onChange={onCheck}
        aria-label={t.includeInSearch(doc.filename)}
      />
      <button className="doc-name" onClick={onSelect} aria-pressed={selected}>
        {doc.filename}
      </button>
      <div className="doc-meta">
        {doc.status === 'ready' && <span className="num">{t.pages(doc.page_count)}</span>}
        {doc.status === 'uploaded' && <span>{t.queued}</span>}
        {doc.status === 'processing' && <span className="tag busy">{t.processing}</span>}
        {note && <span className="tag ocr">OCR</span>}
      </div>
      {note && <div className="doc-note">{note}</div>}
      {doc.status === 'failed' && <div className="doc-note failed">{t.failed}</div>}
      {isPending(doc) && (
        <div className="progress" aria-hidden="true">
          <i />
        </div>
      )}
    </li>
  )
}

function App() {
  const [lang, setLang] = useState<Lang>(initialLang)
  const [documents, setDocuments] = useState<Document[]>([])
  // İlk liste gelene kadar "belge yok" yerine yükleniyor gösterilir.
  const [loadingList, setLoadingList] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  // Yüklenen dosya sırası: [şu anki, toplam]
  const [uploading, setUploading] = useState<[number, number] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploadErrors, setUploadErrors] = useState<{ name: string; key: string }[]>([])
  const [dragging, setDragging] = useState(false)
  const [filter, setFilter] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  // Aramadan çıkarılan belgeler; yeni belgeler varsayılan olarak dahil.
  const [excluded, setExcluded] = useState<Set<number>>(new Set())
  const [pages, setPages] = useState<PageText[] | null>(null)
  const [textError, setTextError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const t = messages[lang]
  const errorText = (key: string) => t.errors[key] ?? key
  const selected = documents.find((d) => d.id === selectedId) ?? null
  const pendingKey = documents.filter(isPending).map((d) => d.id).join(',')
  const ready = documents.filter((d) => d.status === 'ready')
  const searchable = ready.filter((d) => !excluded.has(d.id))
  const query = filter.trim().toLocaleLowerCase(t.locale)
  const shown = query
    ? documents.filter((d) => d.filename.toLocaleLowerCase(t.locale).includes(query))
    : documents

  useEffect(() => {
    document.documentElement.lang = lang
    saveLang(lang)
  }, [lang])

  // Önce ekrana sığacak kadar belge gelir, kalanlar arka planda sayfa sayfa eklenir.
  useEffect(() => {
    let cancelled = false
    async function load() {
      let offset = 0
      let limit = Math.ceil(window.innerHeight / 50)
      try {
        for (;;) {
          const start = offset
          const page = await listDocuments({ offset, limit })
          if (cancelled) return
          // Bu arada yüklenen belge sırayı kaydırabilir; aynı belge iki kez eklenmez.
          setDocuments((docs) => {
            if (start === 0) return page
            const ids = new Set(docs.map((d) => d.id))
            return [...docs, ...page.filter((d) => !ids.has(d.id))]
          })
          setLoadingList(false)
          if (page.length < limit) break
          setLoadingMore(true)
          offset += limit
          limit = PAGE_SIZE
        }
      } catch (e) {
        if (!cancelled) setError((e as Error).message)
      } finally {
        if (!cancelled) {
          setLoadingList(false)
          setLoadingMore(false)
        }
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const block = (e: DragEvent) => {
      if (e.dataTransfer?.types.includes('Files')) e.preventDefault()
    }
    window.addEventListener('dragover', block)
    window.addEventListener('drop', block)
    return () => {
      window.removeEventListener('dragover', block)
      window.removeEventListener('drop', block)
    }
  }, [])

  // İşlenen belgelerin durumu 2 saniyede bir yenilenir; liste yeniden çekilmez.
  useEffect(() => {
    if (!pendingKey) return
    const ids = pendingKey.split(',').map(Number)
    const timer = setInterval(() => {
      listDocuments({ ids })
        .then((updated) => {
          const byId = new Map(updated.map((d) => [d.id, d]))
          setDocuments((docs) => docs.map((d) => byId.get(d.id) ?? d))
        })
        .catch((e) => setError(e.message))
    }, 2000)
    return () => clearInterval(timer)
  }, [pendingKey])

  // Seçili belge hazır olunca metni getirilir.
  useEffect(() => {
    setPages(null)
    setTextError(null)
    if (selectedId === null || selected?.status !== 'ready') return
    getDocumentText(selectedId)
      .then(setPages)
      .catch((e) => setTextError(e.message))
  }, [selectedId, selected?.status])

  function toggle(id: number) {
    setExcluded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  // Dosyalar sırayla yüklenir; biri başarısız olursa diğerleri devam eder.
  async function uploadFiles(files: File[]) {
    if (files.length === 0 || uploading) return
    setUploadErrors([])
    const failed: { name: string; key: string }[] = []
    for (const [i, file] of files.entries()) {
      setUploading([i + 1, files.length])
      try {
        const doc = await uploadDocument(file)
        setDocuments((docs) => [{ ...doc, page_count: 0, ocr_page_count: 0 }, ...docs])
      } catch (e) {
        failed.push({ name: file.name, key: (e as Error).message })
      }
    }
    setUploading(null)
    setUploadErrors(failed)
  }

  function handleFiles(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    e.target.value = ''
    uploadFiles(files)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragging(false)
    uploadFiles(Array.from(e.dataTransfer.files))
  }

  function handleDragLeave(e: React.DragEvent) {
    if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setDragging(false)
  }

  return (
    <div className="app">
      <header className="topbar">
        Kaynakça
        <div className="lang" role="group" aria-label="Language">
          {(['tr', 'en'] as const).map((l) => (
            <button key={l} onClick={() => setLang(l)} aria-pressed={lang === l}>
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </header>

      <div className="layout">
        <aside
          className={dragging ? 'sidebar dragging' : 'sidebar'}
          aria-label={t.searchable}
          onDragOver={(e) => {
            if (!e.dataTransfer.types.includes('Files')) return
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="sidebar-head">
            <span>{t.searchable}</span>
            <span className="count">
              {searchable.length} / {ready.length}
            </span>
          </div>

          {documents.length > 0 && (
            <input
              className="filter"
              type="search"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder={t.filterPlaceholder}
              aria-label={t.filterPlaceholder}
            />
          )}
          <div className="doc-list">
            {loadingList && (
              <p className="hint loading" role="status">
                <span className="spinner" aria-hidden="true" />
                {t.loadingDocuments}
              </p>
            )}
            {!loadingList && !error && documents.length === 0 && <p className="hint">{t.noDocuments}</p>}
            {documents.length > 0 && shown.length === 0 && <p className="hint">{t.noMatch}</p>}
            <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {shown.map((doc) => (
                <DocItem
                  key={doc.id}
                  doc={doc}
                  t={t}
                  checked={doc.status === 'ready' && !excluded.has(doc.id)}
                  selected={doc.id === selectedId}
                  onCheck={() => toggle(doc.id)}
                  onSelect={() => setSelectedId(doc.id)}
                />
              ))}
            </ul>
            {loadingMore && (
              <p className="hint loading" role="status">
                <span className="spinner" aria-hidden="true" />
                {t.loadingMore}
              </p>
            )}
          </div>

          <div className="sidebar-foot">
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              multiple
              onChange={handleFiles}
              hidden
            />
            <button className="add" onClick={() => inputRef.current?.click()} disabled={uploading !== null}>
              {uploading ? t.uploading(...uploading) : t.addDocument}
            </button>
            <p className="hint">{t.addHint}</p>
            {error && (
              <p className="alert" role="alert">
                {errorText(error)}
              </p>
            )}
            {uploadErrors.length > 0 && (
              <ul className="alert" role="alert">
                {uploadErrors.map((f, i) => (
                  <li key={i}>
                    {f.name}: {errorText(f.key)}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>

        <main className="main">
          {!selected ? (
            <div className="empty">
              <h2>{t.emptyTitle}</h2>
              <p>{t.emptyBody}</p>
            </div>
          ) : (
            <section className="detail">
              <div>
                <h2>{selected.filename}</h2>
                <p className="sub">
                  {formatSize(selected.size)} ·{' '}
                  {new Date(selected.created_at).toLocaleString(t.locale)}
                </p>
              </div>

              {selected.content_type === 'application/pdf' ? (
                <iframe
                  className="preview"
                  src={documentFileUrl(selected.id)}
                  title={selected.filename}
                />
              ) : (
                <img className="preview" src={documentFileUrl(selected.id)} alt={selected.filename} />
              )}

              <h3 className="section-title">{t.extractedText}</h3>
              {isPending(selected) && <p className="sub">{t.extracting}</p>}
              {selected.status === 'failed' && (
                <p className="alert" role="alert">
                  {t.failedDetail}
                </p>
              )}
              {textError && (
                <p className="alert" role="alert">
                  {errorText(textError)}
                </p>
              )}
              {pages?.map((p) => (
                <article key={p.page} className="page">
                  <h4 className="page-head">{t.pageHead(p.page, p.text.length)}</h4>
                  <p className="page-text">{p.text || t.emptyPage}</p>
                </article>
              ))}
            </section>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
