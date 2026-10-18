import { useEffect, useRef, useState } from 'react'
import { documentFileUrl, type Answer } from './api'
import type { Messages } from './i18n'

export type Turn = {
  id: number
  question: string
  startedAt: number
  // Sorunun sorulduğu andaki aranacak belge sayısı
  docCount: number
  answer?: Answer
  error?: string
}

export type EvidenceRef = { turnId: number; index: number }

function Elapsed({ since, t }: { since: number; t: Messages }) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [])
  return <>{t.writing(Math.max(0, Math.floor((now - since) / 1000)))}</>
}

export function TurnView({
  turn,
  t,
  active,
  onCite,
  errorText,
}: {
  turn: Turn
  t: Messages
  active: number | null
  onCite: (index: number) => void
  errorText: (key: string) => string
}) {
  const a = turn.answer
  // Aynı sayfaya düşen alıntılar kaynak satırında bir kez gösterilir.
  const pages = a
    ? a.citations
        .map((c, i) => ({ c, i }))
        .filter(({ c }, k, all) => all.findIndex((x) => x.c.filename === c.filename && x.c.page === c.page) === k)
    : []
  const used = a ? a.sources.filter((s) => a.citations.some((c) => c.chunk_id === s.chunk_id)) : []

  return (
    <article className="qa">
      <h2>{turn.question}</h2>
      {!a && !turn.error && (
        <p className="hint loading" role="status">
          <span className="spinner" aria-hidden="true" />
          <Elapsed since={turn.startedAt} t={t} />
        </p>
      )}
      {turn.error && (
        <p className="alert" role="alert">
          {errorText(turn.error)}
        </p>
      )}
      {a?.answered && (
        <>
          <p className="ans">
            {a.answer}
            {a.citations.map((_, i) => (
              <button
                key={i}
                className={active === i ? 'ref on' : 'ref'}
                onClick={() => onCite(i)}
                aria-pressed={active === i}
                aria-label={t.sourceN(i + 1)}
              >
                {i + 1}
              </button>
            ))}
          </p>
          <div className="src">
            {pages.map(({ c, i }) => (
              <button key={i} className="link" onClick={() => onCite(i)}>
                {c.filename}, {t.pageShort} <span className="num">{c.page}</span>
              </button>
            ))}
            <span>{a.unverified_quotes ? t.someUnverified(a.unverified_quotes) : t.verified}</span>
          </div>
        </>
      )}
      {a && !a.answered && <p className="none">{t.refusals[a.refusal ?? ''] ?? t.refusals.not_in_sources}</p>}
      {a && (
        <details className="how">
          <summary>{t.how}</summary>
          <dl>
            <dt>{t.searched}</dt>
            <dd>{t.searchedValue(turn.docCount, a.sources.length)}</dd>
            {a.sources.length > 0 && (
              <>
                <dt>{t.topScore}</dt>
                <dd className="num">{a.sources[0].score.toFixed(2)}</dd>
              </>
            )}
            <dt>{a.answered ? t.used : t.result}</dt>
            <dd>
              {a.answered
                ? t.usedValue(used.length, [...new Set(used.map((s) => s.section).filter(Boolean))].join(', '))
                : t.refusalDetail[a.refusal ?? ''] ?? ''}
            </dd>
          </dl>
        </details>
      )}
    </article>
  )
}

// Alıntı parça içinde büyük/küçük harf, boşluk ve tırnak farkı yok sayılarak aranır.
function highlight(text: string, quote: string): [string, string, string] | null {
  const words = quote.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return null
  const pattern = words
    .map((w) =>
      w
        .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        .replace(/["“”]/g, '["“”]')
        .replace(/['‘’]/g, "['‘’]"),
    )
    .join('\\s+')
  const m = new RegExp(pattern, 'iu').exec(text)
  return m ? [text.slice(0, m.index), m[0], text.slice(m.index + m[0].length)] : null
}

export function Evidence({ turn, index, t }: { turn: Turn | null; index: number | null; t: Messages }) {
  const markRef = useRef<HTMLElement>(null)
  const citation = turn?.answer && index !== null ? turn.answer.citations[index] : null
  const source = citation ? turn?.answer?.sources.find((s) => s.chunk_id === citation.chunk_id) : null
  const parts = source && citation ? highlight(source.text, citation.quote) : null

  useEffect(() => {
    markRef.current?.scrollIntoView({ block: 'center' })
  }, [citation])

  return (
    <aside className="evidence" aria-label={t.evidence}>
      <div className="ev-head">
        <b>{t.evidence}</b>
        {citation && index !== null && <span className="ref on">{index + 1}</span>}
        {citation && (
          <span className="ev-where">
            {citation.filename}, {t.pageShort} <span className="num">{citation.page}</span>
            {' · '}
            <a
              className="link"
              href={`${documentFileUrl(citation.document_id)}#page=${citation.page}`}
              target="_blank"
              rel="noopener"
            >
              {t.openPage}
            </a>
          </span>
        )}
      </div>
      {!citation && <p className="hint">{t.evidenceEmpty}</p>}
      {citation && (
        <div className="ev-card">
          {source?.section && <p className="ev-section">{source.section}</p>}
          {source?.source === 'ocr' && <p className="doc-note">{t.ocrAll}</p>}
          {parts ? (
            <p className="ev-text">
              {parts[0]}
              <mark ref={markRef}>{parts[1]}</mark>
              {parts[2]}
            </p>
          ) : (
            <>
              <p className="ev-text">
                <mark>{citation.quote}</mark>
              </p>
              {source && <p className="ev-text muted">{source.text}</p>}
            </>
          )}
        </div>
      )}
    </aside>
  )
}
