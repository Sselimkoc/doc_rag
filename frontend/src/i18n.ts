export type Lang = 'tr' | 'en'

const tr = {
  locale: 'tr-TR',
  searchable: 'Aranacak belgeler',
  checkAll: 'Tümünü işaretle',
  uncheckAll: 'Tümünü kaldır',
  noDocuments: 'Henüz belge yok.',
  loadingDocuments: 'Belgeler yükleniyor…',
  loadingMore: 'Diğer belgeler yükleniyor…',
  includeInSearch: (name: string) => `${name} aramaya dahil`,
  pages: (n: number) => `${n} sayfa`,
  queued: 'Sırada',
  processing: 'İşleniyor',
  failed: 'Metin çıkarılamadı',
  ocrAll: 'Taramadan okundu, hata olabilir',
  ocrSome: (ocr: number, total: number) => `${ocr} / ${total} sayfa taramadan okundu, hata olabilir`,
  addDocument: '+ Belge ekle',
  uploading: (i: number, n: number) => (n > 1 ? `Yükleniyor… ${i} / ${n}` : 'Yükleniyor…'),
  addHint: 'PDF, JPG veya PNG; birden çok dosya seçebilir ya da buraya sürükleyebilirsiniz. Taranmış belgeler OCR ile okunur.',
  filterPlaceholder: 'Belge adıyla filtrele',
  noMatch: 'Eşleşen belge yok.',
  emptyTitle: 'Belgelerinize soru sorun',
  emptyBody:
    'Cevaplar yalnızca işaretli belgelerden gelir ve her cevap belgeden birebir alıntıyla gösterilir. Belgede olmayan bilgi için cevap üretilmez.',
  question: 'Soru',
  questionPlaceholder: 'Belgelerinize bir soru yazın',
  ask: 'Sor',
  noSearchable: 'Aramak için soldan en az bir hazır belge işaretleyin.',
  writing: (s: number) => `Cevap yazılıyor… ${s} s (yerel model, bir dakika sürebilir)`,
  sourceN: (n: number) => `Kaynak ${n}`,
  pageShort: 's.',
  openPage: 'Sayfayı aç',
  verified: 'Alıntı belgede birebir bulundu',
  someUnverified: (n: number) => `${n} alıntı belgede bulunamadı, gösterilmedi`,
  refusals: {
    no_sources: 'Belgelerde bu bilgi yok.',
    not_in_sources: 'Belgelerde bu bilgi yok.',
    unverified: 'Cevap üretildi ama alıntıları belgede birebir bulunamadı, bu yüzden gösterilmedi.',
  } as Record<string, string>,
  how: 'Nasıl bulundu',
  searched: 'Aranan',
  searchedValue: (docs: number, chunks: number) => `${docs} belge, en yakın ${chunks} parça`,
  topScore: 'En yüksek benzerlik',
  used: 'Kullanılan',
  usedValue: (n: number, sections: string) => `${n} parça${sections ? `: ${sections}` : ''}`,
  result: 'Sonuç',
  refusalDetail: {
    no_sources: 'Soruya yeterince benzeyen parça yok, model çağrılmadı',
    not_in_sources: 'Model parçalarda cevap bulamadı',
    unverified: 'Modelin alıntıları kaynak parçalarda yok',
  } as Record<string, string>,
  evidence: 'Kanıt',
  evidenceEmpty: 'Bir cevaptaki kaynak numarasına tıklayınca alıntının geçtiği metin burada görünür.',
  backToChat: '← Sorular',
  extractedText: 'Çıkarılan metin',
  extracting: 'Metin çıkarılıyor…',
  failedDetail: 'Metin çıkarılamadı. Sunucu loguna bakın.',
  pageHead: (page: number, chars: number) => `Sayfa ${page} · ${chars} karakter`,
  emptyPage: '(Bu sayfadan metin çıkmadı.)',
  errors: {
    list: 'Belgeler alınamadı.',
    upload: 'Yükleme başarısız.',
    unsupported: 'Sadece PDF, JPG ve PNG desteklenir.',
    text: 'Metin alınamadı.',
    answer: 'Cevap alınamadı.',
    ollama: 'Model servisine (Ollama) ulaşılamadı.',
  } as Record<string, string>,
}

const en: typeof tr = {
  locale: 'en-GB',
  searchable: 'Documents to search',
  checkAll: 'Check all',
  uncheckAll: 'Uncheck all',
  noDocuments: 'No documents yet.',
  loadingDocuments: 'Loading documents…',
  loadingMore: 'Loading more documents…',
  includeInSearch: (name) => `Include ${name} in search`,
  pages: (n) => `${n} ${n === 1 ? 'page' : 'pages'}`,
  queued: 'Queued',
  processing: 'Processing',
  failed: 'Text could not be extracted',
  ocrAll: 'Read from a scan, may contain errors',
  ocrSome: (ocr, total) => `${ocr} / ${total} pages read from a scan, may contain errors`,
  addDocument: '+ Add document',
  uploading: (i, n) => (n > 1 ? `Uploading… ${i} / ${n}` : 'Uploading…'),
  addHint: 'PDF, JPG or PNG; select several files or drop them here. Scanned documents are read with OCR.',
  filterPlaceholder: 'Filter by name',
  noMatch: 'No matching documents.',
  emptyTitle: 'Ask your documents',
  emptyBody:
    'Answers come only from the checked documents, each backed by an exact quote. If the documents do not contain the answer, none is given.',
  question: 'Question',
  questionPlaceholder: 'Ask a question about your documents',
  ask: 'Ask',
  noSearchable: 'Check at least one ready document on the left to search.',
  writing: (s) => `Writing the answer… ${s} s (local model, may take a minute)`,
  sourceN: (n) => `Source ${n}`,
  pageShort: 'p.',
  openPage: 'Open page',
  verified: 'Quote found verbatim in the document',
  someUnverified: (n) => `${n} ${n === 1 ? 'quote was' : 'quotes were'} not found in the document and are hidden`,
  refusals: {
    no_sources: 'The documents do not contain this information.',
    not_in_sources: 'The documents do not contain this information.',
    unverified: 'An answer was generated, but its quotes were not found verbatim in the documents, so it is hidden.',
  },
  how: 'How it was found',
  searched: 'Searched',
  searchedValue: (docs, chunks) => `${docs} ${docs === 1 ? 'document' : 'documents'}, ${chunks} closest passages`,
  topScore: 'Top similarity',
  used: 'Used',
  usedValue: (n, sections) => `${n} ${n === 1 ? 'passage' : 'passages'}${sections ? `: ${sections}` : ''}`,
  result: 'Result',
  refusalDetail: {
    no_sources: 'No passage is similar enough to the question; the model was not called',
    not_in_sources: 'The model found no answer in the passages',
    unverified: "The model's quotes are not in the source passages",
  },
  evidence: 'Evidence',
  evidenceEmpty: 'Click a source number in an answer to see the passage it was quoted from.',
  backToChat: '← Questions',
  extractedText: 'Extracted text',
  extracting: 'Extracting text…',
  failedDetail: 'Text could not be extracted. Check the server log.',
  pageHead: (page, chars) => `Page ${page} · ${chars} characters`,
  emptyPage: '(No text was extracted from this page.)',
  errors: {
    list: 'Could not load documents.',
    upload: 'Upload failed.',
    unsupported: 'Only PDF, JPG and PNG are supported.',
    text: 'Could not load text.',
    answer: 'Could not get an answer.',
    ollama: 'Could not reach the model service (Ollama).',
  },
}

export const messages = { tr, en }
export type Messages = typeof tr

export function initialLang(): Lang {
  try {
    const saved = localStorage.getItem('lang')
    if (saved === 'tr' || saved === 'en') return saved
  } catch {
    // localStorage kapalıysa tarayıcı diline düşülür.
  }
  return navigator.language.startsWith('tr') ? 'tr' : 'en'
}

export function saveLang(lang: Lang) {
  try {
    localStorage.setItem('lang', lang)
  } catch {
    // kaydedilemezse sadece bu oturumda geçerli olur
  }
}
