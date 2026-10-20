# Benzer projeler: araştırma raporu

**Tarih:** 2026-10-15

20'ye yakın projeye bakıldı: büyük açık kaynak platformlar, belge dönüştürücüler, OCR kullanmayan görsel RAG projeleri ve Türkçe ya da "kanıt yoksa cevap verme" odaklı küçük projeler.

**Uyarı:** Bilgilerin hepsi README'lerden ve dokümanlardan. Hiçbiri çalıştırılmadı. Özellikle küçük projelerin metrikleri kendi beyanları.

## 1. Projeler ve yaklaşımları

| Proje | Girdi | Nasıl yapıyor | Bizden farkı |
|---|---|---|---|
| **RAGFlow** (92k★, Apache) | PDF, Office, resim, taranmış | DeepDoc: OCR + sayfa düzeni tanıma + tablo yapısı tanıma (3 görsel model); şablona göre parçalama; çoklu arama + yeniden sıralama; izlenebilir alıntılar | 16 GB RAM, Docker. Görsel modellerle sayfa düzeni çıkarıyor |
| **kotaemon** (26k★, Apache) | PDF, HTML, XLSX | Değiştirilebilir dönüştürücü: Docling / PaddleOCR / Azure / Adobe. Kelime + vektör arama, yeniden sıralama. **PDF görüntüleyicide alıntıyı vurgulama**, ilgili sonuç azsa uyarı | Arayüz Gradio. Arayüzden fikir alınacak proje |
| **Docling** (69k★, MIT) | PDF, Office, resim, ses… | Sayfa düzeni + tablo modeli; 6 OCR motoru (RapidOCR, EasyOCR, **Tesseract**…); OCR sadece resim bölgelerine; tam sayfa OCR seçeneği | Hazır dönüştürücü. OCRTurk'te Türkçe karakter skoru 0.71 |
| **Marker** (40k★) | PDF, resim, Office | **Metin katmanını kalite açısından değerlendiriyor**, bozuk ya da taranmış sayfayı görsel-dil modeline (VLM) gönderiyor. Tabloları önce metin katmanından kurallarla kuruyor, olmazsa VLM | Kod Apache, ama **model ağırlıkları $5M gelir üstünde ticari lisans** istiyor |
| **MinerU** (82k★) | PDF, resim, Office | Sayfa düzeni + formül + tablo modelleri; VLM seçeneği | Tam kurulum ≥8 GB VRAM; Apache'ye ek şartlı özel lisans |
| **olmOCR** (AllenAI, 20k★) | PDF, resim | 7B'lik VLM (Qwen2.5-VL), sayfayı Markdown'a çeviriyor; tablo ve el yazısı | ≥12 GB VRAM; İngilizce ağırlıklı |
| **zerox** (12k★, MIT) | PDF, Office, resim | Her sayfayı resim olarak bir API VLM'ine (GPT-4o, Claude, Gemini) gönderip Markdown istiyor | Tamamen API'ye bağımlı. Uydurma metin uyarısı yok |
| **OpenDataLoader PDF** (Apache) | PDF | Java tabanlı, kural bazlı; okuma sırası için XY-Cut++; çıktı **koordinatlı JSON** | Tablo doğruluğu kendi ölçümlerine göre kural modunda 0.489, yapay zekâ destekli modda 0.928 |
| **ColPali / byaldi / VisRAG** | Sayfa resmi | **OCR yok:** sayfa resmi doğrudan vektöre çevriliyor (görsel modelle, sayfa başına çok vektör); cevabı VLM üretiyor | Kökten farklı yaklaşım, aşağıda ayrıca ele alındı |
| **RAG-Anything** (24k★, MIT) | PDF, Office, resim, ses | MinerU/Docling ile ayrıştırıp tablo ve resimleri VLM ile metne açıklatıyor; LightRAG bilgi grafiği | API LLM'e bağımlı |
| **PaperQA2** (9k★, Apache) | PDF, Office | Ajan akışı; parçaları **LLM ile yeniden sıralayıp özetliyor**; metin içi alıntı; tablo ve resimler parçalar arasında bölünmüyor | Bilimsel makalelere özel |
| **turkish_rag_chatbot** (berkecftc) | PDF, DOCX, XLSX, CSV, taranmış resim | **Tesseract tur+eng**; "sayfa başına karakter < eşik → OCR"; BGE-M3 + Postgres Türkçe tam metin arama + RRF (iki sıralamayı birleştirme) + bge-reranker-v2-m3; Ollama qwen2.5:7b; cevaptan sonra cevap–bağlam uyumu kontrolü; Celery kuyruğu | **Bize en yakın proje.** Neredeyse aynı yığın, çok daha büyük altyapı |
| **TR-Docuquery** (TÜBİTAK 2209-A) | PDF, telefon fotoğrafı | **EasyOCR + görüntü ön işleme:** eğiklik düzeltme, gölge giderme, güven skoru < 0.4 olanları atma. Maddeye göre parçalama ("MADDE 6 – FESİH"), dinamik benzerlik eşiği, "belgelerde bulunamadı" | Ölçüm sonucu yok |
| **pdf-qa-assistant** (Erennw) | Metinli PDF (OCR yok) | Çerçeve kullanmadan; Türkçe ve İngilizce arama ölçümü; cevaplanamayan **kontrol soruları** | En iyi belgelenmiş başarısızlıklar burada |
| **document-intelligence-rag** (santos) | PDF, PNG, JPEG | Tesseract; çizgili tablolar; BM25 + vektör + RRF; **alıntı kodda doğrulanıyor: belge, sayfa, kutu koordinatı ve birebir alıntı**; sadece metinden alıntılayan cevaplar; 18 soruluk ölçüm | "Uydurmama" konusunda bize en yakın proje |
| **Turkish-Legal-QA-RAG** (BeratMert29) | Hukuk metinleri | BM25 (Snowball kök bulma) + BGE-M3 + RRF + reranker; QLoRA ile ince ayar; NLI ile cevap–kaynak tutarlılık ölçümü; adım adım karşılaştırma | Önemli bulgu: HF'deki referans cevapların **%25'inin etiketi yanlış** çıkmış |
| **ai-cookbook / hybrid-retrieval** (daveebbelaar) | Kısa metinler (FiQA, 57 bin forum yazısı) | Eğitim: BM25 (bm25s) → vektör → RRF (k=60) → ilk 50 adaya cross-encoder reranker; **her aşama ayrı ölçülüyor** (NDCG@10). Ayrı bir dokümanda kendi belgelerinden LLM ile soru üreterek test seti kurma | Sadece arama; cevap, ret, OCR ve parçalama yok. OpenAI ve Cohere servisleriyle |

## 2. Konu konu bulgular ve bizim için anlamı

### a) "Bu sayfa taranmış mı?" kararı

Bizim zayıf noktamız 1, yani sadece "metin katmanı tamamen boş mu" kontrolü. Diğerleri bunu daha akıllıca yapıyor:

- **turkish_rag_chatbot:** sayfa başına karakter sayısı bir eşiğin altındaysa OCR.
- **jateen321/RAG:** şüpheli belgede 3 sayfayı OCR'layıp metin katmanıyla karşılaştırıyor. Benzerlik 0.4'ün altındaysa tüm belge OCR'a gidiyor. Bu yöntem bozuk font eşlemesini de yakalıyor: metin ekranda doğru görünüyor ama katmanda anlamsız karakterler var.
- **Marker:** metin katmanının kalitesini değerlendiriyor, bozuksa OCR.

→ Bizde iki küçük adım olabilir: önce karakter eşiği, sonra (isteğe bağlı) örnek sayfa karşılaştırması.

### b) OCR motoru

- Bizim ölçeğimizdeki iki Türkçe projeden biri Tesseract tur+eng kullanıyor, diğeri EasyOCR. Tesseract kararımız tek başına bir tercih değil, yaygın bir seçim.
- Büyük dönüştürücülerin hepsi VLM tabanlı OCR'a geçmiş (Marker, olmOCR, MinerU). Gereksinimleri 8–12 GB VRAM ve büyük ölçüde İngilizce/Çince odaklılar; bizim 4 GB GPU + yerel model kısıtımıza uymuyorlar.
- **TR-Docuquery'nin ön işlemesi** (eğiklik düzeltme, gölge giderme, güven skoru filtresi) bizim gerçek telefon fotoğrafı testimize doğrudan uyuyor. Güven skoru filtresi de Vaka 9 3. sayfadaki anlamsız metin için önerilen çözümle aynı.

### c) Tablolar

- **Herkes zorlanıyor.** RAGFlow'da bile taranmış tablolarda içerik kaybı, tekrar ve sütun kayması için açılmış bir düzeltme PR'ı var (#19989; birleştirilmedi, yerine başka bir PR açıldı). Bizim Vaka 9'da gördüğümüz sorunların aynısı.
- **Metin katmanlı PDF'te kurallarla tablo çıkarma** (pdfplumber, Marker'ın ilk adımı, OpenDataLoader) yaygın ve doğru bir ilk adım. VLM'e sadece kurallar başarısız olunca gidiliyor. Bizim pdfplumber kararımız bu sırayla uyumlu.
- **Taranmış tablolar** için olgun projeler ya görsel tablo-yapısı modeli (RAGFlow) ya da VLM (Marker, RAG-Anything) kullanıyor. Kurallarla iyi sonuç alan bir yaklaşım görülmedi. Bu, "bilinen sınır" olarak bırakma önerisini destekliyor.
- PaperQA tabloları parçalar arasında bölmüyor → **bizde de bir tablo tek parça kalmalı.** Parçalama adımında dikkat edilecek.

### d) OCR olmadan görsel RAG (ColPali, VisRAG)

Sayfa resmi doğrudan aranıyor, OCR ve tablo sorunu hiç doğmuyor. Ama bizim için üç engel var:

1. Cevabı üretmek için bir VLM gerekiyor; yerel 7B metin modeli yetmez.
2. **Alıntı doğrulama yapılamaz.** Metin olmadığı için "bu cümle belgede geçiyor mu" kontrolü yok, oysa "uydurmama" gereksinimimizin temeli bu.
3. Türkçe desteği belirsiz; sadece bir topluluk modeli 22 dil desteklediğini söylüyor.

### e) Arama

Neredeyse her ciddi proje aynı formülü kullanıyor:

- **BM25 (kelime arama) + vektör arama + RRF (iki sıralamayı birleştirme) + cross-encoder reranker** (ikinci bir modelin sonuçları yeniden sıralaması).
- Türkçe projelerde BGE-M3 ve bge-reranker-v2-m3.

Erennw'nin ölçümü:

- Türkçede multilingual-e5-base Recall@3'te 0.667, MiniLM 0.333 aldı; çok dilli model iki kat iyi.
- Kimlik numarası gibi değerler (ör. "SP 800-161r1") vektörle hiç bulunamıyor. Bu yüzden **kelime araması şart.** Bizim belgelerde de belge numarası, kod, tutar gibi değerler var.
- Türkçe kelime arama için: Snowball kök bulma (BeratMert29) ya da Postgres'in Türkçe tam metin araması. Planlanan ı→i sadeleştirmesi buna ek olarak gerekecek.

ai-cookbook / hybrid-retrieval (2026-10-17'de eklendi):

- **Vektör veritabanı gerekmiyor:** yazara göre 5 milyon parçanın altında tek bir numpy matrisi vektör veritabanlarından hızlı; üstünde Qdrant, LanceDB ya da pgvector. Bizim exact numpy aramamızla aynı karar.
- **Aşama aşama ölçüm:** her bileşenin katkısı ayrı satırda. Bizde de Dense → BM25 → Hibrit (→ Reranker) tablosu Hit@k, MRR ve soru türüne göre README'ye konacak. Tek kanıt sayfalı sorularda NDCG@10 neredeyse MRR'ye eşit.
- **BM25 neden:** embedding nadir ve kesin terimleri (kod, numara) yumuşatıyor. Bizim setteki örnekler: `FT-2026-00187`, `PaSa-7b`, `alpha = 2.0`, `Tier 1`. Diller arası sorularda BM25 katkı vermez; RRF sıraları birleştirdiği için bozulmaz.
- **Türkçeye uymayan yanı:** bm25s İngilizce ayarlarla kullanılmış. Türkçe ekler için kök bulma ya da ilk n harf gerekir. Uygulama yolu olarak SQLite FTS5 (bağımlılık yok, aynı veritabanı) ile bm25s + PyStemmer karşılaştırıldı; FTS5 tercih edildi.
- **İ küçültmesi:** Python'da `"İ".lower()` "i" + birleştirici nokta veriyor. Kelime aramasında da ele alınmalı (alıntı doğrulamada jet-02'yi bozan hata buydu).
- **Reranker:** yazar Cohere kullanıyor; yerel karşılığı bge-reranker-v2-m3 (yaklaşık 568 MB). Bizdeki asıl değeri cevap vermeme eşiğini netleştirmek olabilir. Maliyeti torch + sentence-transformers (yaklaşık 2 GB) ve 4 GB ekran kartında qwen ile bellek paylaşımı; eşik yetersiz kalırsa düşünülecek.
- **LLM ile soru üretme:** elle yazılmış setimiz daha güvenilir; yalnız "sistemi görmeden yazılmış soru yok" eksiğini kapatmak için birkaç soru bu yolla üretilebilir.

### f) Uydurmama: en önemli bölüm

Görülen yaklaşımlar, zayıftan güçlüye:

1. **Sadece prompt** ("yalnızca bağlamdan cevap ver"): TR-Docuquery.
2. **LLM'den önce benzerlik eşiği:** Erennw. Ama kendi ölçümü bu yöntemin zayıflığını gösteriyor: doğru eşleşmelerin uzaklığı 0.100–0.178, cevaplanamayan soruların 0.153–0.223. Aralıklar **çakışıyor**, yani tek bir eşik yetmiyor.
3. **İlgili sonuç azsa uyarı:** kotaemon.
4. **Cevaptan sonra kontrol:** cevap–bağlam uyumu (berkecftc) ve NLI ile cümle cümle "bu cümle kaynaktan çıkıyor mu" kontrolü (BeratMert29, mDeBERTa).
5. **Alıntıyı kodda doğrulama:** santos ve novshita. Model bir alıntı veriyor, kod bunun belgede birebir geçip geçmediğine bakıyor; geçmiyorsa iddiayı siliyor. santos ayrıca sayfa ve kutu koordinatını da doğruluyor.

→ Bizim eskizdeki plan ("skor düşükse ya da alıntı belgede doğrulanamazsa: belgelerde yok") 2 ve 5'in birleşimi, yani en güçlü uçta. Erennw'nin çakışan aralıkları, eşiğin tek başına yetmediğini kanıtlıyor.

### g) Kaynak vurgulama

kotaemon ve santos alıntıyı belgenin üstünde vurguluyor. Bunun için **çıkarım anında metnin koordinatları saklanmalı:** pdfplumber karakter koordinatlarını, Tesseract `image_to_data` ise kelime kutularını veriyor. Şu an sadece düz metin döndürülüyor. Arayüzde vurgulama isteniyorsa, metni kaydetme adımında koordinatları da saklamak sonradan eklemekten çok daha kolay. Bu kararın metin kaydetme adımından önce verilmesi gerekiyor.

### h) Ölçüm ve test

- **Erennw:** her belge için 6 cevaplanabilir + 2 kontrol sorusu, kategorilere göre: belgedeki ifadeyle, farklı ifadeyle, sayfa sınırına bölünmüş bilgi, gizli ayrıntı, kimlik numarası, farklı kelime seçimi. TESTING.md'deki soru-cevap bölümü için hazır bir şablon.
- **santos:** 18 soru; testlerde döndürülmüş PDF, zararlı metin ve sahte alıntı deneme vakaları da var.
- **BeratMert29:** hazır referans verisine körü körüne güvenmemek gerektiğini gösteriyor; etiketlerin %25'i hatalıymış.

### i) Ölçek

Bu küçük projelerde bile işlem arka planda yapılıyor: Celery kuyruğu, "işleniyor/hazır/hata" durumları. Bizim OCR hâlâ istek anında çalışıyor (zayıf nokta 4). MVP için şimdilik kabul edilebilir, ama yükleme sırasında `status` alanını güncelleme planı bu yaklaşımla aynı yönde.

## 3. Özet

**Doğrulanan kararlar:**

- Tesseract tur+eng
- Metin katmanlı PDF'te kurallarla tablo çıkarma (pdfplumber)
- Hazır dönüştürücü yerine izlenebilir kendi akışımız
- Alıntı doğrulamalı "bilmiyorum"

**Sıradaki adımlar için alınacak fikirler:**

1. Taranmış sayfa tespiti için karakter eşiği.
2. OCR güven skoru filtresi.
3. Metni saklarken koordinatları da saklamak.
4. Arama: BM25 + vektör + RRF + reranker; BGE-M3 ya da multilingual-e5.
5. Bir tablonun tek parça kalması.
6. Kontrol sorulu ölçüm seti.

**"Değerlendirildi, seçilmedi" adayları:**

- VLM tabanlı OCR (Marker, olmOCR, MinerU): GPU ve lisans kısıtları.
- OCR'sız görsel RAG (ColPali, VisRAG): alıntı doğrulanamıyor.
- API ile VLM OCR (zerox): yerel çalışma tercihine aykırı.

## Kaynaklar

Büyük projeler:

- [RAGFlow](https://github.com/infiniflow/ragflow), [RAGFlow PR #19989](https://github.com/infiniflow/ragflow/pull/19989)
- [kotaemon](https://github.com/Cinnamon/kotaemon)
- [Docling](https://github.com/docling-project/docling), [Docling OCR](https://docling-project.github.io/docling/concepts/OCR/)
- [Marker](https://github.com/datalab-to/marker)
- [MinerU](https://github.com/opendatalab/MinerU)
- [olmOCR](https://github.com/allenai/olmocr)
- [zerox](https://github.com/getomni-ai/zerox)
- [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf)
- [ColPali](https://github.com/illuin-tech/colpali), [VisRAG](https://github.com/OpenBMB/VisRAG)
- [RAG-Anything](https://github.com/HKUDS/RAG-Anything)
- [PaperQA2](https://github.com/Future-House/paper-qa)
- [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm)

Türkçe ve küçük projeler:

- [turkish_rag_chatbot](https://github.com/berkecftc/turkish_rag_chatbot)
- [TR-Docuquery](https://github.com/MuhammetDikmetas/TR-Docuquery)
- [pdf-qa-assistant](https://github.com/Erennw/pdf-qa-assistant)
- [Turkish-Legal-QA-RAG](https://github.com/BeratMert29/Turkish-Legal-Question-Answering-RAG)
- [Rag-citation-agent](https://github.com/novshita/Rag-citation-agent)
- [document-intelligence-rag](https://github.com/santosgus3dtech/document-intelligence-rag)
- [jateen321/RAG](https://github.com/jateen321/RAG)

Arama:

- [ai-cookbook / hybrid-retrieval](https://github.com/daveebbelaar/ai-cookbook/tree/main/knowledge/hybrid-retrieval), [bm25s](https://github.com/xhluca/bm25s), [bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3), [RRF makalesi](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
