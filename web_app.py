import streamlit as st
import google.generativeai as genai
import pdfplumber
import os

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="醫療輔具 AI 助理", page_icon="🤖")
st.title("🤖 醫療輔具申請諮詢助手")

# 從 Secrets 讀取 Key (雲端版必備)
API_KEY = st.secrets["GEMINI_API_KEY"]
PDF_PATH = "醫療輔具申請-作業程序.pdf" 

genai.configure(api_key=API_KEY)

# --- 關鍵修正：在雲端請用 1.5-flash，它的免費額度最穩 ---
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. 讀取 PDF 內容 ---
@st.cache_resource
def load_pdf_content(path):
    all_text = ""
    if os.path.exists(path):
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: all_text += text + "\n"
            return all_text
        except Exception as e:
            return f"❌ 讀取 PDF 失敗：{e}"
    return None

knowledge_context = load_pdf_content(PDF_PATH)

# --- 3. 對話介面 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("請問有什麼可以幫您的？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not knowledge_context or knowledge_context.startswith("❌"):
            response_text = "❌ 找不到 PDF 規範檔案，請確認檔案已上傳至 GitHub。"
        else:
            # 這裡用你本機測試成功的 Prompt
            full_prompt = f"你是「榮民服務處」專業助理。請嚴格根據以下規範回答：\n{knowledge_context}\n\n問題：{prompt}"
            try:
                ai_response = model.generate_content(full_prompt)
                response_text = ai_response.text
            except Exception as e:
                response_text = f"❌ AI 連線出錯：{e}"
        
        st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
