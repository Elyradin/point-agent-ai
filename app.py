import re
import streamlit as st

from agent_pdf import (
    PDF_PATH,
    answer_question,
    chunk_text,
    create_vectorstore,
    handle_calculator,
    load_memory,
    read_pdf,
    save_memory,
)

st.set_page_config(page_title="PDF Agent", page_icon="📄", layout="wide")
st.title("AgentAI")

if "memory" not in st.session_state:
    st.session_state.memory = load_memory()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "vectorstore" not in st.session_state:
    try:
        with st.spinner("Membaca dokumen dan menyiapkan indeks..."):
            pdf_text = read_pdf(PDF_PATH)
            if not pdf_text:
                st.error("Dokumen PDF tidak ditemukan atau gagal dibaca.")
                st.stop()

            chunks = chunk_text(pdf_text, chunk_size=500, chunk_overlap=50)
            st.session_state.vectorstore = create_vectorstore(chunks)
    except Exception as exc:
        st.error(f"Gagal menyiapkan agent: {exc}")
        st.stop()

st.sidebar.header("⚙️ Memory")
st.sidebar.write(f"Nama tersimpan: {st.session_state.memory.get('name', '-')}" )

if st.sidebar.button("Reset memory"):
    st.session_state.memory = {}
    save_memory(st.session_state.memory)
    st.sidebar.success("Memory dibersihkan")
    st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input("Tanya tentang dokumen PDF, simpan nama, atau hitung angka")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    q_stripped = prompt.strip()
    q_lower = q_stripped.lower()
    memory = st.session_state.memory

    if not q_stripped:
        assistant_text = "Silakan ketik pertanyaan atau perintah."
    else:
        name_match = re.search(r"nama\s+(?:saya|aku)(?:\s+adalah)?\s+([^.,!?]+)", prompt, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip().rstrip(".?!")
            memory["name"] = name
            save_memory(memory)
            st.session_state.memory = memory
            assistant_text = f"Oke, saya akan ingat nama Anda sebagai {name}."
        else:
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
                    assistant_text = f"Nama Anda adalah {memory['name']}. 😊"
                else:
                    assistant_text = "Saya belum mengetahui nama Anda. Silakan ketik 'Nama saya El' atau 'Nama aku El'."
            else:
                calc_answer = handle_calculator(prompt)
                if calc_answer is not None:
                    assistant_text = calc_answer
                else:
                    assistant_text = answer_question(prompt, st.session_state.vectorstore, memory)

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
    with st.chat_message("assistant"):
        st.write(assistant_text)

    st.rerun()
