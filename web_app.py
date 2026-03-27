import streamlit as st
from google import genai
import pdfplumber
import os

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="醫療輔具 AI 助理", page_icon="🤖")
st.title("🤖 醫療輔具申請諮詢助手")

# --- 2. 使用全新的 Google SDK 連線方式 ---
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)
PDF_PATH = "醫療輔具申請-作業程序.pdf" 

# --- 3. 讀取 PDF 內容 ---
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
            return f"讀取 PDF 發生錯誤: {e}"
    return None

knowledge_context = load_pdf_content(PDF_PATH)

# --- 4. 建立對話紀錄 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. 處理使用者輸入 ---
if prompt := st.chat_input("請問有什麼可以幫您的？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not knowledge_context:
            response_text = "❌ 找不到 PDF 規範檔案，請確認檔案名稱。"
        elif "讀取 PDF 發生錯誤" in knowledge_context:
             response_text = f"❌ 檔案已找到，但無法讀取內容。{knowledge_context}"
        else:
            full_prompt = f"請根據以下規範回答問題：\n{knowledge_context}\n\n問題：{prompt}"
            try:
                # 使用全新的寫法呼叫 AI 模型
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=full_prompt
                )
                response_text = response.text
            except Exception as e:
                response_text = f"出錯了：{e}"
        
        st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
