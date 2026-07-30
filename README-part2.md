# Part 2 — Web Scraper + Summarizer

Bagian ini menambahkan fitur web scraping sederhana yang mengambil isi halaman website, lalu meringkasnya dengan model Gemini melalui Google API key.


## Prasyarat
- Python 3.10+
- API key Google

## Instalasi
1. Masuk ke folder proyek
2. Buat dan aktifkan virtual environment (opsional tapi disarankan)
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependency
   ```powershell
   pip install -r requirements.txt
   ```

## Konfigurasi
Buat file `.env` di root proyek dan isi:
```env
GOOGLE_API_KEY=your_anthropic_api_key_here
```

## Menjalankan scraper
Jalankan file berikut dengan URL target:
```powershell
python scraper.py https://example.com
```

Contoh:
```powershell
python scraper.py https://www.python.org
```

## Hasil
Program akan mencetak ringkasan isi halaman website yang diberikan.

## Bottleneck umum dan solusinya

| Bottleneck umum | Penyebab | Fix |
|---|---|---|
| Gagal di halaman kompleks | Scraper cuma ambil `<body>` mentah | Pakai proper HTML parser (BeautifulSoup) + fallback headless browser (Playwright) untuk halaman dynamic |
| Gagal di konten panjang | Seluruh teks halaman langsung dikirim ke LLM tanpa batas, sehingga context terlalu melebar / token limit error | Chunking + truncation strategy, atau map-reduce summarization (ringkas per chunk, lalu ringkas ulang gabungannya) |
| Summary tidak konsisten panjangnya | Tidak ada constraint eksplisit ke LLM | Guardrail: hard limit token/kata di prompt + post-processing validation (potong ulang kalau LLM tetap kepanjangan) |
| Timeout/crash di halaman berat | Tidak ada retry, tidak ada timeout handling | Try-except per request + ulangi dengan max content size limit |
