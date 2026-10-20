# Test belgeleri

Değerlendirme (`questions.json`) ve ölçümler `testdata/` klasöründeki belgelerle yapılır. Belgeler repoda değil; aşağıdaki adreslerden indirilir. Adresler commit'e sabitlidir, dosyalar SHA-256 ile doğrulanabilir.

## Kaynaklar

| Dosya (`testdata/`) | Kaynak (repo @ commit, yol) | Lisans | Not |
|---|---|---|---|
| `tr_is_kanunu.pdf` | [Erennw/pdf-qa-assistant](https://github.com/Erennw/pdf-qa-assistant) @ `a39b81d`, `data/MevzuatMetin.pdf` | Repo MIT; metin kanun (FSEK md. 31, koruma dışı) | 4857 sayılı İş Kanunu, 55 sayfa. Asıl kaynak: [mevzuat.gov.tr](https://www.mevzuat.gov.tr/MevzuatMetin/1.5.4857.pdf) |
| `en_nist_csf.pdf` | Erennw/pdf-qa-assistant @ `a39b81d`, `data/NIST.CSWP.29.pdf` | Repo MIT; ABD federal yayını | NIST CSF 2.0, 32 sayfa. Asıl kaynak: [nvlpubs.nist.gov](https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf) |
| `tr_sirket_politikasi.pdf` | [berkecftc/turkish_rag_chatbot](https://github.com/berkecftc/turkish_rag_chatbot) @ `ecd620c`, `test_documents/01-metin-sirket-politikasi.pdf` | MIT | Kurgusal şirket politikası |
| `tr_fatura.png` | berkecftc/turkish_rag_chatbot @ `ecd620c`, `test_documents/02-gorsel-fatura.png` | MIT | Kurgusal fatura, OCR |
| `tr_basvuru_formu.pdf` | [MuhammetDikmetas/TR-Docuquery](https://github.com/MuhammetDikmetas/TR-Docuquery) @ `b405431`, `documents/başvuru formu .pdf` | Lisans belirtilmemiş | Sadece bağlantı; yeniden dağıtılmamalı |
| `tr_eksik_veri_avcisi.pdf` | MuhammetDikmetas/TR-Docuquery @ `b405431`, `documents/eksik veri avcısı.pdf` | Lisans belirtilmemiş | Sadece bağlantı |
| `tr_capraz_belge_hakemi.pdf` | MuhammetDikmetas/TR-Docuquery @ `b405431`, `documents/çapraz belge hakemi.pdf` | Lisans belirtilmemiş | Sadece bağlantı |
| `di_shift-handover-scan.pdf` | [santosgus3dtech/document-intelligence-rag](https://github.com/santosgus3dtech/document-intelligence-rag) @ `3be19bf`, `fixtures/shift-handover-scan.pdf` | Repo AGPL-3.0; belgede "CC0 synthetic" | Sadece resim olan PDF (taranmış) |
| `di_shift-handover.png` | aynı repo, `fixtures/shift-handover.png` | aynı | Yukarıdakinin resmi |
| `di_untrusted-instruction.pdf` | aynı repo, `fixtures/untrusted-instruction.pdf` | aynı | Talimat gömülü belge (prompt injection testi) |
| `di_aster-maintenance.pdf` | aynı repo, `fixtures/aster-maintenance.pdf` | aynı | Kısa İngilizce belge |
| `di_recebimento-materiais.pdf` | aynı repo, `fixtures/recebimento-materiais.pdf` | aynı | Portekizce, tablo |
| `di_restricted-planning.pdf` | aynı repo, `fixtures/restricted-planning.pdf` | aynı | Kısa İngilizce belge |
| `kotaemon_table.pdf` | [Cinnamon/kotaemon](https://github.com/Cinnamon/kotaemon) @ `9ad3e4e`, `libs/kotaemon/tests/resources/table.pdf` | Apache-2.0 | Japonca tablo; soru yok, havuzda |
| `kotaemon_multimodal.pdf` | Cinnamon/kotaemon @ `9ad3e4e`, `libs/kotaemon/tests/resources/multimodal.pdf` | Apache-2.0 | Metin + resim + tablo |
| `kotaemon_7810d908b0ff4ce381dcab873196d133.jpg` | Cinnamon/kotaemon @ `9ad3e4e`, `libs/kotaemon/tests/resources/7810d908b0ff4ce381dcab873196d133.jpg` | Apache-2.0 | JPG |
| `paperqa_paper.pdf` | [Future-House/paper-qa](https://github.com/Future-House/paper-qa) @ `57e89f7`, `tests/stub_data/paper.pdf` | Apache-2.0 | Akademik makale, 41 sayfa |
| `paperqa_pasa.pdf` | Future-House/paper-qa @ `57e89f7`, `tests/stub_data/pasa.pdf` | Apache-2.0 | İki sütunlu makale, 15 sayfa |
| `paperqa_duplicate_media.pdf` | Future-House/paper-qa @ `57e89f7`, `tests/stub_data/duplicate_media.pdf` | Apache-2.0 | Tekrar eden resimler |

Ham dosya adresi: `https://raw.githubusercontent.com/<repo>/<commit>/<yol>` (yoldaki boşluk ve Türkçe karakterler URL kodlanır). Tam commit'ler:

- Erennw/pdf-qa-assistant `a39b81d8eaf8b0e1b5c9d1a2b916c823b2177d51`
- berkecftc/turkish_rag_chatbot `ecd620c45980c41a1a290f77c723f79d849319ff`
- MuhammetDikmetas/TR-Docuquery `b40543141e47733d0fe71cf7cb3cb7ae3a85e369`
- santosgus3dtech/document-intelligence-rag `3be19bf13ae201cd03e633ad0946b399822e5216`
- Cinnamon/kotaemon `9ad3e4e49aa35b8acddd235918a5d9753c1cfdf9`
- Future-House/paper-qa `57e89f7223b0960d5ee5ea048c69e3c47e088572`

Dosyalar 2026-10-15'te indirildi; bu commit'lerdeki halleriyle aynı oldukları git blob hash'iyle doğrulandı.

## Repoda olmayan belgeler

- Kişisel belgeler değerlendirmede kullanılmaz; ölçümlerde sadece sayılar raporlanır.

## SHA-256

```
cd75c7fe92bd438443549c3e973e7ea6d03137e9a6bb2652aded52a8ca95e84e  tr_is_kanunu.pdf
3c31f46fee98cac0c4323453e5109291a213b4de7fef8c058af9bf67f717433c  en_nist_csf.pdf
0e31f94a926923e8cba9c85304713c8eda9d58ee53b0b99463b4c4e468d4d711  tr_sirket_politikasi.pdf
763dbde614611485c9d64551ce49260371357984453cd48fb077b57d0fb76fec  tr_fatura.png
0a785679e77f420a04bdc570a62f555c5c01a322b9f7018735c33f0f4c77d6cd  tr_basvuru_formu.pdf
676c728de1b271c1734e4e3cbbc3d471c6b6781d37564578df580e7ba523a15f  tr_eksik_veri_avcisi.pdf
bb0af9b5c2323b851c6db524aba8cbcaf85811cfa04b903319d58623ba291af0  tr_capraz_belge_hakemi.pdf
5ada52ca4fc5f9b0ae0c17e78adb7a7fb4feb63cb2e0d87868ab54b52cc294e2  di_shift-handover-scan.pdf
b91ddf5b96fed646e5c26208ea8ddae0b90b7e6d3e8d20d148fb35f3afb308d8  di_shift-handover.png
2cb8f9a3d33824cbe21b10742ab7ffebc6e4c4da48a2bc03b59702e14aa44543  di_untrusted-instruction.pdf
80c8c05e4cb08107596988b1606bd52161d9c0ae76a5c55def8e8c124227cdec  di_aster-maintenance.pdf
ed502a5163217efd8263d09a5c20d686f0c4f65e623c8e5706b480f39d39214c  di_recebimento-materiais.pdf
f9b0a11e7cb718123217a6e45f1171cb8dba70136ce8b366d59fda89772b6810  di_restricted-planning.pdf
e1765fdf0e2cecb68841dde75ac61dc25071037bd8645984267c5b684669de3d  kotaemon_table.pdf
095b4cc72c11b0dfa91306a07a47c296a010eba883173e3c57ca8434b72ed4fc  kotaemon_multimodal.pdf
bb7b3dbad5674edd1e7389966ab3cb5d2fee1d4f02c3fc419deceb3a44e9616a  kotaemon_7810d908b0ff4ce381dcab873196d133.jpg
145c91b72086b5cde6b048e4b50c7b325c7e1b8c6260e4e91fbc12fcf177eaf3  paperqa_paper.pdf
3979809118c8636e3148d836da89dffd6716afa616f458a1111d76e2301cfc85  paperqa_pasa.pdf
632d5115da4a0095b595c74616ca8272f7e585106fde62f3e1da78da276c268e  paperqa_duplicate_media.pdf
```

`testdata/` içinde `sha256sum -c` ile doğrulanır (bu bloğu bir dosyaya kopyalayarak).
