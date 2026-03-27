import streamlit as st
import google.generativeai as genai
import pdfplumber
import os

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="醫療輔具 AI 助理", page_icon="🤖")
st.title("🤖 醫療輔具申請諮詢助手")
st.info("💡 系統已連線：根據桃園市榮服處規範提供諮詢")

# 讀取金鑰
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
PDF_PATH = "醫療輔具申請-作業程序.pdf" 

# --- 2. 核心修正：自動偵測「有額度且存在」的 3.1 模型 ---
@st.cache_resource
def get_best_model():
    try:
        # 抓取所有這把 Key 認得的模型
        all_models = [m.name for m in genai.list_models()]
        # 根據你的額度表，優先找 3.1-flash-lite 的各種變體名稱
        for m_name in all_models:
            if "3.1-flash-lite" in m_name:
                return m_name.replace("models/", "")
        # 如果找不到 3.1，找 2.5 做保底
        for m_name in all_models:
            if "2.5-flash" in m_name:
                return m_name.replace("models/", "")
        return "gemini-2.5-flash" # 最後的最後才用這個
    except:
        return "gemini-2.5-flash"

TARGET_MODEL = get_best_model()
st.caption(f"🔧 系統目前自動配對最穩定模型：{TARGET_MODEL}")
model = genai.GenerativeModel(TARGET_MODEL)

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

# 顯示歷史紀錄
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 處理提問
if prompt := st.chat_input("請問想了解哪種輔具的申請規則？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not knowledge_context:
            st.error("❌ 找不到 PDF 規範檔案，請確認檔案已上傳。")
        else:
            # 這是你原本最專業的 Prompt
            full_prompt = f"""
            你是「榮民服務處」的專業 AI 客服助理。請嚴格根據下方的【作業規範內容】回答問題。
            
            【規則】：
            1. 如果規範中有提到答案，請詳細列出重點（如：年限、申請條件）。
            2. 如果規範中「完全沒有」提到，請回答：「很抱歉，手冊中未記載此資訊，建議洽詢專員。」
            
            【作業規範內容】：
            {knowledge_context}
            
            【客人的問題】：{prompt}
            """
            try:
                ai_response = model.generate_content(full_prompt)
                st.markdown(ai_response.text)
                st.session_state.messages.append({"role": "assistant", "content": ai_response.text})
            except Exception as e:
                # 如果 500 次也爆了，我們就看錯誤訊息
                st.error(f"❌ AI 暫時無法回應：{e}")
