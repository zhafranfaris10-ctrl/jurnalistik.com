JURNALISTIK SEKOLAH - VERSI REVISI

CARA MENJALANKAN (Windows / VS Code)
1. Ekstrak ZIP ini.
2. Buka folder jurnalistik_revisi di VS Code.
3. Buka Terminal, pastikan terminal berada di folder proyek.
4. Buat virtual environment:
   py -3.14 -m venv .venv
   (Jika Python 3.14 tidak tersedia, gunakan: python -m venv .venv)
5. Install kebutuhan:
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
6. Jalankan:
   .\.venv\Scripts\python.exe app.py
7. Buka browser: http://127.0.0.1:5000

LOGIN DEMO ADMIN
Username: admin
Password: jurnalistikmode

Ganti password demo sebelum website dipublikasikan. Jangan publikasikan server debug Flask.
Untuk penggunaan online, atur SECRET_KEY yang kuat dan gunakan hosting/server produksi.

ISI FITUR
- Home, Karya, Kirim Karya, Saran, Login Admin.
- Upload karya: PDF, DOC, DOCX, JPG, JPEG, PNG (maksimal 10 MB).
- Admin dapat memberi nilai 0-100, feedback, dan status Menunggu/Ditolak/Diterbitkan.
- File yang belum diterbitkan hanya dapat diunduh admin.
- Poster QR yang diberikan pengguna berada di static/images/poster-kirim-karya.jpg.
- QR poster mengarah ke Google Drive pengumpulan karya yang sudah tertanam pada poster.

CATATAN
Database SQLite jurnalistik.db dibuat otomatis saat aplikasi pertama kali dijalankan.


DEPLOY KE RENDER (ONLINE)
1. Upload semua isi folder ini ke satu repository GitHub (jangan upload folder induk).
2. Di Render pilih New > Web Service, lalu hubungkan repository tersebut.
3. Runtime: Python 3
4. Build Command: pip install -r requirements.txt
5. Start Command: gunicorn app:app
6. Tambahkan Environment Variable SECRET_KEY dengan nilai acak yang panjang.
7. Klik Create Web Service.

PENTING: Paket ini memakai SQLite dan menyimpan file upload di folder lokal.
Penyimpanan lokal Render Free bersifat sementara; data/karya upload bisa hilang saat
restart atau deploy. Jangan gunakan untuk pengumpulan karya sungguhan sebelum
database dan file upload dipindahkan ke penyimpanan permanen.
