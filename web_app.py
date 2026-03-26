import streamlit as st
import google.generativeai as genai
import pdfplumber
import os

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="醫療輔具 AI 助理", page_icon="🤖")
st.title("🤖 醫療輔具申請諮詢助手")
st.caption("根據作業程序手冊提供專業回覆")

# --- 2. API 與檔案設定 ---
# 改成從雲端密碼箱讀取
API_KEY = st.secrets["GEMINI_API_KEY"] # 記得換成你的 KEY
PDF_PATH = "醫療輔具申請-作業程序.pdf" 

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 3. 讀取 PDF 內容 (使用緩存避免重複讀取) ---
@st.cache_resource
def load_pdf_content(path):
    all_text = ""
    if os.path.exists(path):
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text: all_text += text + "\n"
        return all_text
    return None

knowledge_context = load_pdf_content(PDF_PATH)

# --- 4. 建立對話紀錄 (讓 AI 記得之前的對話) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# 在網頁上顯示之前的對話
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. 處理使用者輸入 ---
if prompt := st.chat_input("請問有什麼可以幫您的？"):
    # 顯示使用者的問題
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 生成 AI 回覆
    with st.chat_message("assistant"):
        if not knowledge_context:
            response_text = "❌ 找不到 PDF 規範檔案，請確認檔案位置。"
        else:
            full_prompt = f"請根據以下規範回答問題：\n{knowledge_context}\n\n問題：{prompt}"
            try:
                ai_response = model.generate_content(full_prompt)
                response_text = ai_response.text
            except Exception as e:
                response_text = f"出錯了：{e}"
        
        st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})