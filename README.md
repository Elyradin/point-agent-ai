# point-agent-ai

Project ini adalah aplikasi agent PDF berbasis Python yang dapat:
- membaca dokumen PDF,
- menyimpan memori nama pengguna,
- menjawab pertanyaan berdasarkan isi PDF,
- menangani pertanyaan matematika melalui Gemini,
- dijalankan lewat antarmuka Streamlit.

## Prasyarat
- Python 3.10+
- pip
- Akun Google AI Studio untuk mendapatkan API key Gemini

## Instalasi
1. Buka terminal di folder proyek.
2. Buat virtual environment (opsional tapi disarankan):
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   Untuk Windows PowerShell:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependency:
   ```bash
   pip install -r requirements.txt
   ```

## Konfigurasi environment
Buat file `.env` di root proyek dengan isi berikut:
```env
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

Pastikan file `document.pdf` ada di folder proyek.

## Menjalankan aplikasi
### Mode terminal
```bash
python agent_pdf.py
```

### Mode web (Streamlit)
```bash
streamlit run app.py
```

Setelah itu buka browser ke alamat:
```text
http://localhost:8501
```

## Struktur file penting
- `agent_pdf.py` — logika PDF agent, memory, routing, dan Gemini
- `app.py` — antarmuka Streamlit
- `document.pdf` — dokumen PDF yang dibaca
- `requirements.txt` — daftar dependency

## Catatan
- Jika API key belum valid, aplikasi akan menampilkan pesan error dari Gemini.
- Memory disimpan dalam file `memory.json` secara lokal.
