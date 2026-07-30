# Part 1 – AI Email Agent Workflow

## Overview

Branch ini berisi perancangan workflow AI Email Agent untuk mengotomatisasi proses penanganan email pelanggan. Workflow dirancang agar email dapat diprioritaskan, diklasifikasikan, dijawab berdasarkan knowledge base, atau diteruskan ke agen manusia jika diperlukan.

---

## Workflow Diagram
(workfllow-diagram.png)

---

## Workflow Explanation

| Step | Process | Description |
|------|---------|-------------|
| 1 | Receive Email | Sistem menerima email dari pelanggan. |
| 2 | Critical Check | AI memeriksa apakah email bersifat kritis atau pelanggan telah menghubungi lebih dari tiga kali. |
| 3 | Human Agent | Jika kondisi kritis, email diteruskan ke agen manusia untuk penanganan lebih lanjut. |
| 4 | Email Classification | Jika tidak kritis, AI mengklasifikasikan kategori email (misalnya refund, order, shipping, atau complaint). |
| 5 | Knowledge Retrieval | Sistem melakukan pencarian informasi yang relevan dari knowledge base menggunakan pendekatan Retrieval-Augmented Generation (RAG). |
| 6 | Relevance Check | AI mengevaluasi apakah informasi yang ditemukan cukup relevan untuk menjawab pertanyaan pelanggan. |
| 7 | Template Response | Jika informasi tidak cukup relevan, sistem mengirimkan template jawaban atau respons standar. |
| 8 | Response Generation | Jika informasi relevan, AI menyusun jawaban berdasarkan knowledge base. |
| 9 | Final Validation | Jawaban diperiksa kembali sebelum dikirim kepada pelanggan. |
| 10 | Send Response | Sistem mengirimkan jawaban akhir kepada pelanggan. |

---

## Technologies

| Component | Technology |
|-----------|------------|
| Workflow Design | Draw.io |
| LLM | Gemini 3.6 Flash |
| Knowledge Base | PDF / Internal Documentation |
| Retrieval | Chroma Vector Database |
| Embedding | Gemini Embedding 001 |
| PDF Processing | PyPDF2 |
| Text Chunking | RecursiveCharacterTextSplitter |
| User Interface | Streamlit |
| Programming Language | Python |

---

## AI Features

- Email classification
- Retrieval-Augmented Generation (RAG)
- Knowledge Base Search
- Human Handoff
- AI Response Generation
- Final Response Validation
