import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import {
  askQuestion,
  deleteDocument,
  documentFileUrl,
  getDocumentText,
  listDocuments,
  reprocessDocument,
  uploadDocument,
  type Document,
  type PageText,
} from './api'
import { Evidence, TurnView, type EvidenceRef, type Turn } from './Chat'
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
  onReprocess,
  onRemove,
}: {
  doc: Document
  t: Messages
  checked: boolean
  selected: boolean
  onCheck: () => void
  onSelect: () => void
  onReprocess: () => void
  onRemove: () => void
}) {
  const note = ocrNote(doc, t)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // Menü dışına tıklanınca ya da Esc ile kapanır.
  useEffect(() => {
    if (!menuOpen) return
    const close = (e: MouseEvent | KeyboardEvent) => {
      if (e instanceof KeyboardEvent ? e.key === 'Escape' : !menuRef.current?.contains(e.target as Node))
        setMenuOpen(false)
    }
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', close)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('keydown', close)
    }
  }, [menuOpen])

  function choose(action: () => void) {
    setMenuOpen(false)
    action()
  }
  return (
    <li className={selected ? 'doc selected' : 'doc'}>
      <input
        id={`doc-${doc.id}`}
        type="checkbox"
        checked={checked}
        disabled={doc.status !== 'ready'}
        onChange={onCheck}
        aria-label={t.includeInSearch(doc.filename)}
      />
      {/* Ada tıklamak aramaya dahil etmeyi değiştirir; görüntüleme ⋯ menüsünde. */}
      <label className="doc-name" htmlFor={`doc-${doc.id}`}>
        {doc.filename}
      </label>
      <div className="doc-menu" ref={menuRef}>
        <button
          className="more"
          onClick={() => setMenuOpen((open) => !open)}
          aria-haspopup="menu"
          aria-expanded={menuOpen}
          aria-label={t.docActions(doc.filename)}
        >
          ⋯
        </button>
        {menuOpen && (
          <div className="menu" role="menu">
            <button role="menuitem" onClick={() => choose(onSelect)}>
              {t.view}
            </button>
            <button role="menuitem" onClick={() => choose(onReprocess)} disabled={isPending(doc)}>
              {t.reprocess}
            </button>
            <button role="menuitem" className="danger" onClick={() => choose(onRemove)} disabled={isPending(doc)}>
              {t.remove}
            </button>
          </div>
        )}
      </div>
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
  const [turns, setTurns] = useState<Turn[]>([])
  const [question, setQuestion] = useState('')
  const [evidence, setEvidence] = useState<EvidenceRef | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const turnsRef = useRef<HTMLDivElement>(null)
  // Kullanıcı eski mesajlara çıkmadıysa akış en altta tutulur.
  const stickToBottom = useRef(true)

  const t = messages[lang]
  const errorText = (key: string) => t.errors[key] ?? key
  const selected = documents.find((d) => d.id === selectedId) ?? null
  const pendingKey = documents.filter(isPending).map((d) => d.id).join(',')
  const ready = documents.filter((d) => d.status === 'ready')
  const searchable = ready.filter((d) => !excluded.has(d.id))
  const query = filter.trim().toLocaleLowerCase(t.locale)
  const asking = turns.some((turn) => !turn.answer && !turn.error)
  const evidenceTurn = turns.find((turn) => turn.id === evidence?.turnId) ?? null
  const shown = query
    ? documents.filter((d) => d.filename.toLocaleLowerCase(t.locale).includes(query))
    : documents
  // Filtre varsa toplu işaretleme yalnızca görünen hazır belgelere uygulanır.
  const shownReady = shown.filter((d) => d.status === 'ready')
  const allShownChecked = shownReady.every((d) => !excluded.has(d.id))

  useEffect(() => {
    document.documentElement.lang = lang
    saveLang(lang)
  }, [lang])

  // Önce ekrana sığacak kadar belge gelir, kalanlar arka planda sayfa sayfa eklenir.
  useEffect(() => {
    let cancelled = false
    async function load() {
      let offset = 0
      // Pencere gizliyken innerHeight 0 olabilir.
      let limit = Math.max(1, Math.ceil(window.innerHeight / 50))
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

  useLayoutEffect(() => {
    const el = turnsRef.current
    if (el && stickToBottom.current) el.scrollTop = el.scrollHeight
  }, [turns, selectedId])

  function handleTurnsScroll() {
    const el = turnsRef.current
    if (el) stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80
  }

  async function ask(e: React.FormEvent) {
    e.preventDefault()
    const text = question.trim()
    if (!text || asking || searchable.length === 0) return
    const id = Date.now()
    setQuestion('')
    setSelectedId(null)
    stickToBottom.current = true
    setTurns((all) => [...all, { id, question: text, startedAt: id, docCount: searchable.length }])
    // Hiçbir belge çıkarılmadıysa filtre gönderilmez; arka planda henüz gelmemiş belgeler de aranır.
    const ids = excluded.size > 0 ? searchable.map((d) => d.id) : null
    try {
      const answer = await askQuestion(text, ids)
      setTurns((all) => all.map((turn) => (turn.id === id ? { ...turn, answer } : turn)))
      if (answer.citations.length > 0) setEvidence({ turnId: id, index: 0 })
    } catch (err) {
      setTurns((all) => all.map((turn) => (turn.id === id ? { ...turn, error: (err as Error).message } : turn)))
    }
  }

  function toggle(id: number) {
    setExcluded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleAll() {
    setExcluded((prev) => {
      const next = new Set(prev)
      for (const d of shownReady) {
        if (allShownChecked) next.add(d.id)
        else next.delete(d.id)
      }
      return next
    })
  }

  async function removeDocument(doc: Document) {
    if (!window.confirm(t.confirmRemove(doc.filename))) return
    try {
      await deleteDocument(doc.id)
      setDocuments((docs) => docs.filter((d) => d.id !== doc.id))
      if (selectedId === doc.id) setSelectedId(null)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  async function reprocess(doc: Document) {
    try {
      await reprocessDocument(doc.id)
      setDocuments((docs) => docs.map((d) => (d.id === doc.id ? { ...d, status: 'uploaded' } : d)))
    } catch (e) {
      setError((e as Error).message)
    }
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
            <span className="head-actions">
              {shownReady.length > 0 && (
                <button className="link" onClick={toggleAll}>
                  {allShownChecked ? t.uncheckAll : t.checkAll}
                </button>
              )}
              <span className="count">
                {searchable.length} / {ready.length}
              </span>
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
                  onReprocess={() => reprocess(doc)}
                  onRemove={() => removeDocument(doc)}
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
          {selected ? (
            <div className="scroll">
              <button
                className="link back"
                onClick={() => {
                  stickToBottom.current = true
                  setSelectedId(null)
                }}
              >
                {t.backToChat}
              </button>
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
            </div>
          ) : (
            <div className="chat">
              <div className={turns.length ? 'turns has-turns' : 'turns'} ref={turnsRef} onScroll={handleTurnsScroll}>
                {turns.length === 0 ? (
                  <div className="empty">
                    <h2>{t.emptyTitle}</h2>
                    <p>{t.emptyBody}</p>
                  </div>
                ) : (
                  turns.map((turn) => (
                    <TurnView
                      key={turn.id}
                      turn={turn}
                      t={t}
                      active={evidence?.turnId === turn.id ? evidence.index : null}
                      onCite={(index) => setEvidence({ turnId: turn.id, index })}
                      errorText={errorText}
                    />
                  ))
                )}
              </div>
              <form className="ask" onSubmit={ask}>
                <label htmlFor="question">{t.question}</label>
                <div className="ask-row">
                  <input
                    id="question"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder={t.questionPlaceholder}
                    autoComplete="off"
                  />
                  <button className="btn" disabled={!question.trim() || asking || searchable.length === 0}>
                    {t.ask}
                  </button>
                </div>
                {!loadingList && searchable.length === 0 && <p className="hint">{t.noSearchable}</p>}
              </form>
            </div>
          )}
        </main>

        <Evidence turn={evidenceTurn} index={evidenceTurn ? (evidence?.index ?? null) : null} t={t} />
      </div>
    </div>
  )
}

export default App
