import streamlit as st
import google.generativeai as genai
import pdfplumber
import os

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="醫療輔具 AI 助理", page_icon="🤖")
st.title("🤖 醫療輔具申請諮詢助手")

# 讀取金鑰
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
PDF_PATH = "醫療輔具申請-作業程序.pdf" 

# --- 2. 核心修正：自動尋找可用模型 (避免 404) ---
@st.cache_resource
def get_working_model():
    try:
        # 直接抓出這把金鑰「真正權限內」的所有模型
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順序：1.5-flash > 2.0-flash > 1.5-pro > 任何清單裡的第一個
        if "models/gemini-1.5-flash" in models:
            return "gemini-1.5-flash"
        elif "models/gemini-2.0-flash" in models:
            return "gemini-2.0-flash"
        elif "models/gemini-1.5-pro" in models:
            return "gemini-1.5-pro"
        else:
            # 如果都沒抓到預期的，就抓清單裡第一個（去掉 models/ 前綴）
            return models[0].split("/")[-1]
    except Exception as e:
        st.error(f"無法取得模型清單：{e}")
        return "gemini-1.5-flash" # 保底，但通常走到這代表 Key 有問題

working_model_name = get_working_model()
st.caption(f"🔧 系統自動配對模型：{working_model_name}")
model = genai.GenerativeModel(working_model_name)

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
            return f"❌ 讀取 PDF 失敗：{e}"
    return None

knowledge_context = load_pdf_content(PDF_PATH)

# --- 4. 對話介面 ---
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
        if not knowledge_context:
            response_text = "❌ 找不到 PDF 規範檔案，請確認檔案已上傳。"
        else:
            full_prompt = f"請根據以下規範回答問題：\n{knowledge_context}\n\n問題：{prompt}"
            try:
                ai_response = model.generate_content(full_prompt)
                response_text = ai_response.text
            except Exception as e:
                response_text = f"❌ AI 連線出錯：{e}"
        
        st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
