import streamlit as st
import google.generativeai as genai
import os

# ==============================================================================
# PENGATURAN API KEY DAN MODEL
# ==============================================================================

# Ambil API Key dari Streamlit Secrets
# Ini adalah cara yang aman untuk menangani kunci API saat deployment.
# Nama secret di Streamlit Cloud harus 'GEMINI_API_KEY'
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("Error: API Key Gemini tidak ditemukan. Harap tambahkan 'GEMINI_API_KEY' ke Streamlit Secrets Anda.")
    st.stop() # Hentikan eksekusi aplikasi jika API Key tidak ada.

# Nama model Gemini yang akan digunakan.
MODEL_NAME = 'gemini-1.5-flash'

# ==============================================================================
# KONTEKS AWAL CHATBOT
# ==============================================================================

# Definisikan peran chatbot Anda di sini.
INITIAL_CHATBOT_CONTEXT = [
    {
        "role": "user",
        "parts": ["Kamu adalah ahli analisa gempa bumi. Tugasmu adalah memberikan informasi akurat dan ilmiah tentang gempa bumi, tanda-tanda, penyebab, dampak, serta panduan keselamatan. Jika ditanya mengenai data gempa terkini, selalu arahkan pengguna ke situs resmi BMKG atau lembaga geologi terpercaya lainnya. Tolak pertanyaan yang tidak relevan dengan topik gempa bumi atau yang bersifat personal/emosional dengan sopan."]
    },
    {
        "role": "model",
        "parts": ["Halo! Saya adalah ahli analisa gempa bumi. Saya siap memberikan informasi akurat dan panduan terkait gempa bumi. Apa yang ingin Anda ketahui hari ini?"]
    }
]

# ==============================================================================
# FUNGSI INISIALISASI MODEL DAN CHAT
# ==============================================================================

@st.cache_resource
def initialize_gemini_model():
    """
    Menginisialisasi model Gemini dan mengembalikan objek model.
    Menggunakan st.cache_resource agar model hanya diinisialisasi sekali.
    """
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=500
            )
        )
        return model
    except Exception as e:
        st.error(f"Kesalahan saat menginisialisasi model Gemini: {e}")
        st.stop()

# ==============================================================================
# APLIKASI STREAMLIT UTAMA
# ==============================================================================

st.set_page_config(
    page_title="Chatbot Ahli Sejarah",
    page_icon="📚"
)

st.title("📚 Chatbot Ahli Sejarah")
st.markdown("Saya adalah ahli sejarah! Berikan tanggal (DD/MM) dan saya akan ceritakan 2 kejadian menarik di tanggal tersebut.")

# Inisialisasi model Gemini (ini akan dijalankan sekali berkat @st.cache_resource)
gemini_model = initialize_gemini_model()

# Inisialisasi riwayat chat di st.session_state
# Ini penting agar riwayat chat tetap ada saat aplikasi direfresh
if "chat_history_gemini" not in st.session_state:
    st.session_state.chat_history_gemini = list(INITIAL_CHATBOT_CONTEXT) # Salin konteks awal
    st.session_state.messages = []
    # Tambahkan pesan pembuka dari bot ke UI setelah inisialisasi awal
    st.session_state.messages.append({"role": "assistant", "content": INITIAL_CHATBOT_CONTEXT[1]["parts"][0]})

# Tampilkan pesan dari riwayat chat di UI
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ambil input dari pengguna
user_input = st.chat_input("Masukkan tanggal (contoh: 01/01)...")

if user_input:
    # Tambahkan pesan pengguna ke riwayat UI dan tampilkan
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Dapatkan respons dari model Gemini
    with st.chat_message("assistant"):
        with st.spinner("Sedang mencari fakta sejarah..."):
            try:
                # Perbarui chat_history_gemini untuk model Gemini dengan input pengguna
                st.session_state.chat_history_gemini.append({"role": "user", "parts": [user_input]})

                # Mulai sesi chat dengan riwayat yang ada
                chat = gemini_model.start_chat(history=st.session_state.chat_history_gemini)
                response = chat.send_message(user_input, request_options={"timeout": 60})

                if response and response.text:
                    bot_response = response.text
                else:
                    bot_response = "Maaf, saya tidak bisa memberikan balasan."
                st.markdown(bot_response)

                # Tambahkan respons bot ke riwayat UI dan riwayat Gemini
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                st.session_state.chat_history_gemini.append({"role": "model", "parts": [bot_response]})

            except Exception as e:
                st.error(f"Maaf, terjadi kesalahan saat berkomunikasi dengan Gemini: {e}")
                st.markdown("Kemungkinan penyebab: masalah koneksi, API Key tidak valid, atau melebihi kuota.")
