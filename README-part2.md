# Part 2 — Web Scraper + Summarizer

Bagian ini menambahkan fitur web scraping sederhana yang mengambil isi halaman website, lalu meringkasnya dengan model Anthropic Claude.

## Apa yang bisa dilakukan
- Mengambil konten HTML dari URL tertentu
- Membersihkan isi halaman dengan BeautifulSoup
- Mengirim teks ke model Claude untuk dibuat ringkasan

## Prasyarat
- Python 3.10+
- API key Anthropic

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
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Menjalankan scraper
Jalankan file berikut dengan URL target:
```powershell
python broken_scraper.py https://example.com
```

Contoh:
```powershell
python broken_scraper.py https://www.python.org
```

## Hasil
Program akan mencetak ringkasan isi halaman website yang diberikan.

## Catatan
- Skrip ini sederhana dan cocok untuk pembelajaran.
- Untuk website yang memblokir bot, mungkin perlu menambahkan header User-Agent atau teknik scraping yang lebih advanced.
- Pastikan Anda memiliki izin untuk mengambil konten dari website yang dituju.
