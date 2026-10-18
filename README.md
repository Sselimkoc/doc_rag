# doc_rag

PDF, JPG ve PNG belgeler üzerinde Türkçe ve İngilizce soru cevaplayan, tamamen yerel çalışan bir RAG sistemi. Cevaplar yalnızca yüklenen belgelere dayanır. Her cevap, belgeden birebir alıntıyla desteklenir ve alıntı kodda doğrulanır. Kanıt yoksa sistem cevap vermez.

## Ne yapar

- **Metin çıkarma:** metin katmanlı PDF'ler pypdfium2 ile okunur, tablolar pdfplumber ile bulunup Markdown'a çevrilir. Metin katmanı olmayan sayfalar (taranmış PDF) ve resimler Tesseract (`tur+eng`) ile OCR'dan geçer. PDF içine gömülü resimlerdeki yazılar da okunur.
- **Parçalama:** başlıklar (PDF yer imleri ya da yazı tipi) ve paragraflar korunur. Tablolar bölünmez; büyük tablolarda her parçada başlık satırı tekrarlanır.
- **Arama:** bge-m3 embedding'leri, numpy ile tam (yaklaşık olmayan) kosinüs araması. Arama belgelere göre filtrelenebilir.
- **Cevap:** en yakın 6 parça numaralandırılıp modele verilir. Model JSON şemasına uymaya zorlanır (`answerable`, `answer`, `citations[{source, quote}]`).
- **Doğrulama:** her alıntı, gösterdiği kaynak parçada birebir aranır (büyük/küçük harf, tırnak, boşluk ve Unicode biçimi eşitlenerek). Doğrulanamayan alıntı atılır; hiç alıntı kalmazsa cevap reddedilir.

Ret nedenleri ayrı kodlarla döner:

| Kod | Anlamı |
|---|---|
| `no_sources` | Soruyla ilgili parça yok (en yakın parçanın skoru eşiğin altında) |
| `not_in_sources` | Model kaynaklarda cevap bulamadı |
| `unverified` | Modelin alıntıları kaynaklarda birebir bulunamadı |

Skor eşiği (0,44) bge-m3 için değerlendirme setinde ölçülerek seçildi. Belgelerle ilgisiz soruları eler; konusu yakın ama cevabı belgede olmayan soruları ayıramaz (skorları cevaplanabilen sorularla iç içe), onları model reddeder. Başka bir embedding modelinde eşik yeniden ölçülmeli.

## Mimari

```
Belge ─► metin çıkarma (pypdfium2 / pdfplumber / Tesseract)
      ─► parçalama ─► bge-m3 embedding ─► SQLite (belge, sayfa, parça, vektör)

Soru ─► bge-m3 ─► kosinüs araması (ilk 6) ─► skor eşiği
     ─► qwen2.5 (JSON şeması) ─► alıntı doğrulama ─► cevap + kaynaklar
```

- Backend: FastAPI, SQLModel/SQLite. Vektörler aynı SQLite dosyasında. Vektör veritabanı kullanılmadı: bu ölçekte tek bir numpy matrisi hem yeterli hem daha hızlı.
- Model çağrıları: Ollama (yerel). Hiçbir veri dışarı gönderilmez.
- Arayüz: React 19 + Vite. Solda belgeler (yükleme, sürükle-bırak, aranacak belgeleri seçme), ortada soru-cevap, sağda alıntının parça içinde vurgulandığı kanıt paneli.

## Kurulum

Gereksinimler:

- Python 3.11+ ve [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com)
- [Tesseract](https://github.com/tesseract-ocr/tesseract), Türkçe dil paketiyle (`tur`)
- Node.js (arayüz için)

```bash
uv sync
```

```bash
ollama pull bge-m3
```

```bash
ollama pull qwen2.5:14b-instruct-q4_K_M
```

Ayarlar için `.env.example` dosyasını `.env` olarak kopyalayın. Boş bırakılan değerler varsayılanı kullanır. Tesseract PATH'te değilse `TESSERACT_CMD` ile tam yolunu verin.

## Çalıştırma

Backend (http://localhost:8000):

```bash
uv run uvicorn app.main:app --port 8000
```

Arayüz (http://localhost:5173):

```bash
cd frontend && npm install && npm run dev
```

Yüklenen belgeler ve veritabanı `data/` klasöründe tutulur. Açılışta yarıda kalmış ya da işlenmemiş belgeler arka planda yeniden işlenir.

### API

| Uç nokta | Açıklama |
|---|---|
| `POST /documents` | Belge yükleme (PDF, JPG, PNG; en fazla 50 MB, ilk baytları türüne uymalı); işleme arka planda |
| `GET /documents` | Belgeler ve işleme durumları |
| `GET /documents/{id}/file` | Orijinal dosya |
| `GET /documents/{id}/text` | Sayfa sayfa çıkarılan metin (metin katmanı mı OCR mı) |
| `DELETE /documents/{id}` | Belgeyi siler: listeden ve aramadan kalkar, veritabanında `is_deleted` ile kalır |
| `POST /documents/{id}/reprocess` | Belgeyi yeniden işler (ör. işlenemeyen belge) |
| `POST /search` | Anlamsal arama, isteğe bağlı belge filtresi |
| `POST /answer` | Doğrulanmış alıntılarla cevap ya da ret kodu |

## Değerlendirme

`eval/questions.json` içinde 24 belge üzerine elle yazılmış 90 soru var. Türleri: belgede geçen bilgi, diller arası soru, günlük dil ve bozuk yazım, cevaplanamayan soru, genel bilgi tuzağı (cevap belgede yok ama model biliyor), OCR, tablo, birden çok belge ve talimat gömülü belge (prompt injection). Test belgelerinin kaynakları ve lisansları `eval/sources.md` dosyasında.

```bash
uv run python eval/retrieval.py
```

```bash
uv run python eval/answers.py
```

Ölçümler ayrı bir indekste (`eval/.index`) yapılır; `data/` klasörüne dokunulmaz.

Sonuçlar (90 soru):

| Model | Toplam | Cevaplanabilen | Cevaplanamayan | Günlük dil | Medyan süre |
|---|---|---|---|---|---|
| qwen2.5:7b-instruct | 56/90 | 43/77 | 13/13 | 4/11 | 21 s |
| qwen2.5:14b-instruct-q4_K_M | 75/90 | 63/77 | 12/13 | 9/11 | 51 s |

14B satırında OCR'lı belgeleri kullanan 7 soru, taranmış sayfaların satır satır okunmasından (`--psm 4`) sonra yeniden ölçüldü (önce 72/90; fatura soruları alıntı doğrulanamadığı için reddediliyordu).

14B'nin kalan 15 hatası:

- **Arama (9):** cevabı içeren parça ilk 6'ya girmiyor. 4'ünde aynı sayfanın başka bir parçası geliyor; sayfa doğru, cevap cümlesi gelmeyen parçada.
- **OCR (1):** faturadaki "%20" "9020" okunuyor; model oranı kendisi hesaplayıp "%27" yazıyor.
- **Üretim (4):** cevap cümlesi modele verilen parçada olduğu halde yanlış ya da eksik cevap. İkisi aynı cümleden: "1939'da … 1937'de … He 178 ile bir deneme uçuşu yaptılar"; model 1937'yi seçiyor.
- **Uydurma (1):** "Türkiye'nin başkenti neresidir?" sorusuna "Ankara" cevabı. Model, Ankara'nın yalnızca adının geçtiği bir cümleyi alıntıladı (aşağıda, Bilinen sınırlamalar).

## Donanım notu

Ölçümler 4 GB ekran kartı (RTX 3050 Ti) ve 32 GB RAM'li bir dizüstü bilgisayarda yapıldı. Model ekran kartına sığmadığı için çoğu CPU'da çalışıyor:

| Model | Ekran kartında | Soru başına |
|---|---|---|
| qwen2.5:7b-instruct (5,4 GB) | ~%40 | 20–36 s |
| qwen2.5:14b-instruct-q4_K_M (10 GB) | ~%21 | medyan 51 s, en uzun 119 s |

Varsayılan model 14B, çünkü 7B uzun bağlamda kaynak metni tekrar tekrar kopyalayan bir döngüye giriyor ve cevap çıktı sınırında kesiliyor. Hız gerekiyorsa `.env` dosyasında `LLM_MODEL=qwen2.5:7b-instruct` seçilebilir. 8 GB ve üstü ekran kartında 14B tamamen ekran kartına sığar.

## Testler

```bash
uv run pytest --cov
```

Testler geçici bir veri klasörü ve bellekte SQLite kullanır; Ollama çağrıları sahte fonksiyonlarla değiştirilir. Daha önce bulunan hataların her biri için bir regresyon testi var.

## Bilinen sınırlamalar

- Alıntı doğrulaması alıntının belgede birebir geçtiğini kanıtlar, cevabı desteklediğini değil. 14B, Ankara'nın yalnızca adının geçtiği bir cümleyi alıntılayıp "başkent Ankara'dır" diyebildi.
- Cevap metninin kendisi doğrulanmıyor, sadece alıntılar. Model doğru cümleyi alıntılayıp cevapta farklı bir sayı yazabiliyor (7B: "ikiyüzyetmiş" → 276; 14B bu soruyu doğru cevapladı).
- Taranmış sayfalar satır satır okunuyor (Tesseract `--psm 4`): fatura ve formlarda etiket ile değeri aynı satırda kalıyor, ama iki sütunlu taranmış sayfalarda iki sütunun satırları birbirine karışabilir.
- Eğiklik düzeltme yok. Faturanın eğik kopyalarında okunan 6 satırdan 2°'de 4'ü, 5°'de 2'si, 10°'de hiçbiri kaldı. Düşük kontrast daha az etkiliyor (yazı %10 kontrastta 5/6).
- Arama yalnızca anlamsal. Kod ve numara gibi kesin terimler için kelime araması (BM25) henüz yok.
- Yeniden sıralayıcı (bge-reranker-v2-m3) ve hibrit arama (FTS5 + RRF, embedding'e başlık ekleme) denendi: cevabı içeren parça ilk 6'da 67/79'dan 71–72/79'a çıktı, ama cevapta kazanç 1–2 soruda kaldı. Yeniden sıralayıcı soru başına ~18 s ve 2,3 GB model, hibrit arama ek karmaşıklık getirdiği için eklenmedi.
- Kanıt panelinde parça metni gösteriliyor ve kaynak sayfa PDF görüntüleyicide açılabiliyor; sayfa görüntüsü üzerinde vurgulama yok.
- Cevap model bitirince bir kerede geliyor (akış yok); 14B'de bu 30-120 s bekleme demek.

## Klasörler

```
app/        backend (çıkarma, parçalama, embedding, arama, cevap)
frontend/   arayüz
eval/       değerlendirme betikleri, sorular, test belgesi kaynakları
tests/      pytest
```
