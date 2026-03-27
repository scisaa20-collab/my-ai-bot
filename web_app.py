import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import pdfplumber
import os

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="榮民業務智慧導航", page_icon="🏛️")

# --- 2. 終極 CSS (針對 2026 版本) ---
st.markdown(
    """
    <style>
    /* 強制隱藏所有可能抓到的工具列元素 */
    header, footer {visibility: hidden !important; display: none !important;}
    .stAppDeployButton {display: none !important;}
    div[data-testid="stAppToolbar"] {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    
    /* 針對手機版做最後的底部空白修復 */
    .main .block-container {padding-bottom: 0rem !important;}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🏛️ 榮民服務智慧諮詢助理")
st.info("💡 歡迎使用！我是助理小助，目前使用 **Gemma 3** 為您服務。")

# --- 3. 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 系統設定")
    choice = st.selectbox("選擇大腦：", ["Gemma 3", "Gemini 3 Flash", "xAI Grok"])
    
    engine, m_id, grok_client = "", "", None
    if choice == "Gemma 3":
        engine, m_id = "GEMINI", "gemma-3-27b-it" 
    elif choice == "Gemini 3 Flash":
        engine, m_id = "GEMINI", "gemini-3-flash-preview"
    else:
        engine = "GROK"
        try:
            grok_client = OpenAI(api_key=st.secrets["XAI_API_KEY"], base_url="https://api.x.ai/v1")
            models_data = grok_client.models.list().data
            m_id = st.selectbox("👉 請選擇 Grok 版本：", [m.id for m in models_data]) if models_data else "grok-2"
        except: m_id = "grok-2"
    st.success(f"目前運行：{m_id}")

# --- 4. 讀取 PDF ---
PDF_PATH = "醫療輔具申請-作業程序.pdf"
@st.cache_resource
def get_pdf_text():
    if os.path.exists(PDF_PATH):
        try:
            with pdfplumber.open(PDF_PATH) as pdf:
                return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        except: return ""
    return ""
context = get_pdf_text()

# --- 5. 對話紀錄 ---
if "chat" not in st.session_state: st.session_state.chat = []
for m in st.session_state.chat:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 6. 發送提問 ---
if prompt := st.chat_input("您想了解哪項業務申請呢？"):
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # Persona 設定
        sys = "你現在是榮服處助理小助，請溫馨、分點回答規範內容。若沒提到請委婉告知並引導撥電話。"
        full_p = f"{sys}\n\n【規範】\n{context}\n\n【問題】\n{prompt}"
        try:
            with st.spinner("小助正在翻閱規範..."):
                if engine == "GEMINI":
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    ans = genai.GenerativeModel(m_id).generate_content(full_p).text
                else:
                    ans = grok_client.chat.completions.create(model=m_id, messages=[{"role": "user", "content": full_p}]).choices[0].message.content
            st.markdown(ans)
            st.session_state.chat.append({"role": "assistant", "content": ans})
        except Exception as e:
            st.error(f"❌ 連線失敗：{str(e)}")
