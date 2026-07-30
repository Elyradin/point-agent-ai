import os
import json
import re
import ast
import math
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

try:
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
except ImportError:
    ChatGoogleGenerativeAI = None
    GoogleGenerativeAIEmbeddings = None

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

print("✅ Konfigurasi Gemini siap!")
print(f"📌 Model: {gemini_model}")
if not google_api_key:
    print("⚠️ GOOGLE_API_KEY atau GEMINI_API_KEY belum diatur. Tambahkan ke file .env")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(BASE_DIR, "document_hb.pdf")
MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")

DEBUG = False

def log(msg):
    if DEBUG:
        print(msg)


def read_pdf(pdf_path):
    log(f"📄 Membaca PDF: {pdf_path}")
    
    try:
        reader = PdfReader(pdf_path)
        text = ""
        
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        log(f"✅ Berhasil baca {len(reader.pages)} halaman")
        log(f"📊 Total karakter: {len(text):,}")
        return text
    
    except FileNotFoundError:
        log(f"❌ File tidak ditemukan: {pdf_path}")
        return None
    except Exception as e:
        log(f"❌ Error baca PDF: {e}")
        return None


def load_memory():
    try:
        if not os.path.exists(MEMORY_PATH):
            return {}
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_memory(mem: dict):
    try:
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(mem, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"⚠️ Gagal menyimpan memory: {e}")


def evaluate_expression(expression: str):
    expr = expression.strip()
    if not expr:
        raise ValueError("Ekspresi kosong")

    allowed_names = {
        "pi": math.pi,
        "e": math.e,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "ln": math.log,
        "abs": abs,
    }

    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.FloorDiv):
                return left // right
            if isinstance(node.op, ast.Mod):
                return left % right
            if isinstance(node.op, ast.Pow):
                return left ** right
            raise ValueError("Operator tidak didukung")
        if isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            raise ValueError("Unary operator tidak didukung")
        if isinstance(node, ast.Name):
            if node.id in allowed_names:
                return allowed_names[node.id]
            raise ValueError(f"Nama tidak didukung: {node.id}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in allowed_names and len(node.args) == 1:
                return allowed_names[func_name](_eval(node.args[0]))
            raise ValueError("Fungsi tidak didukung")
        raise ValueError("Ekspresi tidak didukung")

    try:
        parsed = ast.parse(expr, mode="eval")
        result = _eval(parsed.body)
        if isinstance(result, float) and result.is_integer():
            return int(result)
        return result
    except Exception as exc:
        raise ValueError(f"Tidak bisa menghitung: {exc}") from exc


def handle_calculator(question: str):
    q = question.strip()
    if not q:
        return None

    q_lower = q.lower()
    if not any(keyword in q_lower for keyword in ["hitung", "kalkulator", "berapa", "berapakah", "hasil", "calc"]):
        if not re.search(r"[\d)\]]", q_lower):
            return None

    m = re.search(r"([0-9\s\+\-\*\/\(\)\.]+)", q)
    if m:
        expr = m.group(1).strip()
        if re.search(r"[\d]", expr) and any(op in expr for op in ["+", "-", "*", "/", "%", "(", ")"]):
            try:
                result = evaluate_expression(expr)
                return f"Hasil perhitungan: {result}"
            except ValueError as exc:
                return str(exc)

    return None

def chunk_text(text, chunk_size=500, chunk_overlap=50):
    log(f"✂️ Memecah teks menjadi chunk (size={chunk_size})...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    
    chunks = text_splitter.split_text(text)
    log(f"✅ Terpecah menjadi {len(chunks)} chunk")
    
    return chunks

def create_vectorstore(chunks):
    log("🗄️ Membuat Vector Store...")

    if GoogleGenerativeAIEmbeddings is None:
        raise ImportError("Paket langchain-google-genai belum terinstall. Jalankan: pip install langchain-google-genai")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY/GEMINI_API_KEY belum diatur")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        google_api_key=google_api_key,
    )
    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory="./pdf_db"
    )
    
    log("✅ Vector Store siap!")
    return vectorstore

def answer_question(question, vectorstore, memory):
    log(f"🔍 Mencari informasi untuk: '{question[:50]}...'")
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(question)
    
    if not docs:
        return "❌ Maaf, saya tidak menemukan informasi tentang itu di PDF."
    
    context = "\n\n---\n\n".join([doc.page_content for doc in docs])
    
    memory_note = ""
    if memory and isinstance(memory, dict) and memory.get("name"):
        memory_note = (
            f"Nama pengguna adalah {memory.get('name')}. "
            "Sapa pengguna dengan nama tersebut jika sesuai."
        )

    prompt = f"""
    Anda adalah asisten yang membantu berdasarkan dokumen PDF.

    {memory_note}

    Pertanyaan: {question}

    Konten dari PDF (hanya bagian yang relevan):
    {context}

    Instruksi:
    1. Jawab BERDASARKAN konten PDF di atas
    2. Jika informasi tidak lengkap, katakan dengan jujur
    3. JANGAN menambahkan informasi di luar PDF
    4. Jawab dengan bahasa Indonesia yang ramah

    Jawaban:
    """
    
    log("💬 Menghasilkan jawaban...")
    try:
        if ChatGoogleGenerativeAI is None:
            return "❌ Paket langchain-google-genai belum terinstall. Jalankan: pip install langchain-google-genai"
        if not google_api_key:
            return "❌ GOOGLE_API_KEY/GEMINI_API_KEY belum diatur"

        llm = ChatGoogleGenerativeAI(
            model=gemini_model,
            google_api_key=google_api_key,
        )
        response = llm.invoke(prompt)

        content = getattr(response, "content", response)

        if isinstance(content, list):
            return "\n".join(
                item["text"]
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            )

        return str(content)
    except Exception as e:
        return f"❌ Gagal menghubungi Gemini: {e}\nPastikan API key valid dan model '{gemini_model}' tersedia."

def main():
    log("="*60)
    log("🤖 AGENT DENGAN PDF")
    log("="*60)
    log()
    
    pdf_text = read_pdf(PDF_PATH)
    if not pdf_text:
        log("❌ Gagal membaca PDF. Pastikan file ada.")
        return
    
    chunks = chunk_text(pdf_text, chunk_size=500, chunk_overlap=50)
    
    vectorstore = create_vectorstore(chunks)
    
    log("\n" + "="*60)
    log("✅ PDF siap! Silakan bertanya...")
    log("="*60 + "\n")
    
    memory = load_memory()

    while True:
        question = input("\n👤 Anda: ")
        q_stripped = question.strip()
        q_lower = q_stripped.lower()

        if q_lower in ["exit", "quit", "keluar"]:
            log("👋 Sampai jumpa!")
            break

        if not q_stripped:
            continue

        m = re.search(
            r"nama\s+(?:saya|aku)(?:\s+adalah)?\s+([^.,!?]+)",
            question,
            re.IGNORECASE,
        )
        if m:
            name = m.group(1).strip()
            name = re.sub(r'[\.\?!]$', '', name).strip()
            memory['name'] = name
            save_memory(memory)
            log(f"✅ Oke, saya akan ingat nama Anda sebagai: {name}")

        name_questions = [
            "siapa nama saya",
            "siapa nama aku",
            "siapa namaku",
            "ingat nama saya",
            "ingat nama aku",
            "apakah kamu ingat nama saya",
            "apakah kamu ingat nama aku",
            "kamu ingat nama saya",
            "kamu ingat nama aku",
        ]

        if any(q in q_lower for q in name_questions):
            if memory.get("name"):
                log(f"\n🤖 Agent: Nama Anda adalah {memory['name']}. 😊")
            else:
                log("\n🤖 Agent: Saya belum mengetahui nama Anda. Silakan ketik 'Nama saya El' atau 'Nama aku El'.")
            continue

        calc_answer = handle_calculator(question)
        if calc_answer is not None:
            log(f"\n🤖 Agent: {calc_answer}")
            continue

        answer = answer_question(question, vectorstore, memory)
        log(f"\n🤖 Agent: {answer}")
if __name__ == "__main__":
    main()