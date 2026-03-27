import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import pdfplumber
import os

# --- 1. 網頁基礎設定 ---
st.set_page_config(
    page_title="榮民業務智慧導航", 
    page_icon="🏛️", 
    layout="centered"
)

# --- 2. 終極視覺優化：隱藏所有官方標籤 (包含手機版皇冠、連線圖示與 Embed 底標) ---
hide_st_style = """
            <style>
            /* 1. 隱藏上方裝飾線、選單與部署按鈕 */
            header {visibility: hidden; display: none !important;}
            #MainMenu {visibility: hidden; display: none !important;}
            .stDeployButton {display: none !important;}
            div[data-testid="stDecoration"] {display: none !important;}
            
            /* 2. 隱藏底部所有標籤 (含 "Made with Streamlit" 與 Embed 模式底標) */
            footer {visibility: hidden; display: none !important;}
            div[data-testid="stFooter"] {display: none !important;}
            div[data-testid="stEmbedFooter"] {display: none !important;}
            #streamlit_status_details {display: none !important;}
            
            /* 3. 針對手機版：強力隱藏右下角工具列 (紅皇冠與綠圈圈) */
            div[data-testid="stAppToolbar"] {display: none !important;}
            button[title="Manage app"] {display: none !important;}
            button[title="View menu"] {display: none !important;}
            
            /* 4. 調整間距，讓畫面更緊湊專業 */
            .main .block-container {padding-top: 2rem !important; padding-bottom: 0rem !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 3. 網頁標題與歡迎語 ---
st.title("🏛️ 榮民服務智慧諮詢助理")
st.info("💡 您好！我是小助。目前預設使用 **Gemma 3** 為您服務。")

# --- 4. 側邊欄：保留模型選單 ---
with st.sidebar:
    st.header("⚙️ 系統設定")
    # 模型選單保留在左側
    choice = st.selectbox(
        "請選擇 AI 大腦：",
        ["Gemma 3", "Gemini 3 Flash", "xAI Grok"]
    )
    
    engine, m_id, grok_client = "", "", None

    if choice == "Gemma 3":
        engine, m_id = "GEMINI", "gemma-3-27b-it" 
    elif choice == "Gemini 3 Flash":
        engine, m_id = "GEMINI", "gemini-3-flash-preview"
    else:
        # xAI Grok 動態偵測
        engine = "GROK"
        try:
            grok_client = OpenAI(
                api_key=st.secrets["XAI_API_KEY"],
                base_url="https://api.x.ai/v1"
            )
            models_data = grok_client.models.list().data
            live_grok_models = [m.id for m in models_data]
            if live_grok_models:
                m_id = st.selectbox("👉 請選擇 Grok 版本：", live_grok_models)
            else:
                m_id = "grok-2"
        except:
            m_id = "grok-2"
    
    st.success(f"目前運行：{m_id}")

# --- 5. 讀取 PDF 文字 ---
PDF_PATH = "醫療輔具申請-作業程序.pdf"
@st.cache_resource
def get_pdf_text():
    if os.path.exists(PDF_PATH):
        try:
            with pdfplumber.open(PDF_PATH) as pdf:
                return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        except:
            return ""
    return ""

context = get_pdf_text()

# --- 6. 對話紀錄 ---
if "chat" not in st.session_state:
    st.session_state.chat = []

for m in st.session_state.chat:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 7. 發送提問與 AI 回覆 ---
if prompt := st.chat_input("您想了解哪項業務申請呢？"):
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 溫暖專員 Persona 設定
        system_instruction = """
        你現在是「桃園市榮民服務處」的專業 AI 助理，名字叫「小助」。
        請根據提供的規範內容，用溫暖、耐心且清晰的方式回答。
        1. 語氣親切，稱對方為「您」。
        2. 分點說明，讓排版簡潔。
        3. 規範沒寫的，請引導聯繫榮服處，不亂編造。
        """
        
        full_p = f"{system_instruction}\n\n【規範內容】\n{context}\n\n【問題】\n{prompt}"
        
        try:
            with st.spinner("小助正在為您翻閱手冊..."):
                if engine == "GEMINI":
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel(m_id)
                    res = model.generate_content(full_p)
                    ans = res.text
                else:
                    res = grok_client.chat.completions.create(
                        model=m_id, 
                        messages=[{"role": "user", "content": full_p}]
                    )
                    ans = res.choices[0].message.content

            st.markdown(ans)
            st.session_state.chat.append({"role": "assistant", "content": ans})
        except Exception as e:
            st.error(f"❌ 連線失敗：{str(e)}")
