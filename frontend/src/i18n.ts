export type Lang = 'tr' | 'en'

const tr = {
  locale: 'tr-TR',
  searchable: 'Aranacak belgeler',
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
  emptyTitle: 'Belge seçin',
  emptyBody: 'Soldaki listeden bir belge seçerek önizlemesini ve çıkarılan metni görebilirsiniz.',
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
  } as Record<string, string>,
}

const en: typeof tr = {
  locale: 'en-GB',
  searchable: 'Documents to search',
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
  emptyTitle: 'Select a document',
  emptyBody: 'Pick a document from the list on the left to see its preview and extracted text.',
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
