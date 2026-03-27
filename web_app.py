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

# --- 2. 核心修正：模型診斷與手動選擇器 ---
with st.sidebar:
    st.header("⚙️ 系統設定")
    try:
        # 抓取這把 Key 真正能用的所有模型 ID
        available_models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 讓使用者自己選，預設幫你找 3.1 或 1.5
        default_idx = 0
        for i, name in enumerate(available_models):
            if "3.1-flash-lite" in name or "1.5-flash" in name:
                default_idx = i
                break
        
        selected_model = st.selectbox("請選擇 AI 模型 (若報錯請切換)", available_models, index=default_idx)
        st.info(f"當前模型：{selected_model}")
        model = genai.GenerativeModel(selected_model)
    except Exception as e:
        st.error(f"無法讀取模型清單：{e}")
        st.stop()

# --- 3. 讀取 PDF 內容 ---
@st.cache_resource
def load_pdf_content():
    if os.path.exists(PDF_PATH):
        try:
            with pdfplumber.open(PDF_PATH) as pdf:
                text = ""
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
            return text
        except: return None
    return None

knowledge_context = load_pdf_content()

# --- 4. 對話介面 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("請問想了解哪種輔具的申請規則？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not knowledge_context:
            st.error("❌ 找不到 PDF 規範檔案。")
        else:
            full_prompt = f"請根據以下規範回答問題：\n{knowledge_context}\n\n問題：{prompt}"
            try:
                ai_response = model.generate_content(full_prompt)
                st.markdown(ai_response.text)
                st.session_state.messages.append({"role": "assistant", "content": ai_response.text})
            except Exception as e:
                st.error(f"❌ 此模型連線出錯：{e}")
                st.warning("💡 提示：可能是額度用盡或模型名稱不對，請從左側選單換一個模型試試！")
