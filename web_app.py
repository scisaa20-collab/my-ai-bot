import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import pdfplumber
import os

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="榮民業務智慧導航", page_icon="🏛️")

# --- 2. 終極視覺美化：強力隱藏所有官方標籤與工具列 ---
# 這裡使用了最嚴格的 CSS 選擇器，試圖從底層抹除皇冠與連線圖示
hide_st_style = """
            <style>
            /* 隱藏上方裝飾線 */
            div[data-testid="stDecoration"] {display: none !important;}
            
            /* 隱藏選單按鈕與部署按鈕 */
            #MainMenu {visibility: hidden; display: none !important;}
            .stDeployButton {display: none !important;}
            header {visibility: hidden; display: none !important;}
            
            /* 隱藏底部 "Made with Streamlit" */
            footer {display: none !important;}
            div[data-testid="stFooter"] {display: none !important;}
            
            /* 【核心修正】強力隱藏手機版右下角的工具列 (紅皇冠與綠圈圈所在處) */
            div[data-testid="stAppToolbar"] {display: none !important;}
            button[title="View menu"] {display: none !important;}
            
            /* 針對手機版可能殘留的透明區塊進行最後清除 */
            .st-emotion-cache-1wbqy5l {display: none !important;}
            .st-emotion-cache-1vt458u {display: none !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("🏛️ 榮民服務智慧諮詢助理")
st.info("💡 您好！我是小助。目前預設使用 **Gemma 3** 為您服務，這是一個既聰明又穩定的選擇。")

# --- 3. 側邊欄：模型設定與自動偵測 ---
with st.sidebar:
    st.header("⚙️ 系統設定")
    # 預設首選為 Gemma 3
    choice = st.selectbox(
        "請選擇 AI 大腦：",
        ["Gemma 3", "Gemini 3 Flash", "xAI Grok"]
    )
    
    engine = ""
    m_id = ""
    grok_client = None

    if choice == "Gemma 3":
        engine, m_id = "GEMINI", "gemma-3-27b-it" 
    elif choice == "Gemini 3 Flash":
        engine, m_id = "GEMINI", "gemini-3-flash-preview"
    else:
        # xAI Grok 自動偵測邏輯
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

# --- 4. 讀取 PDF 文字 ---
PDF_PATH = "醫療輔具申請-作業程序.pdf"
@st.cache_resource
def get_pdf_text():
    if os.path.exists(PDF_PATH):
        try:
            with pdfplumber.open(PDF_PATH) as pdf:
                return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        except Exception as e:
            return f"讀取錯誤：{e}"
    return ""

context = get_pdf_text()

# --- 5. 對話紀錄顯示 ---
if "chat" not in st.session_state:
    st.session_state.chat = []

for m in st.session_state.chat:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 6. 發送提問與 AI 回覆 ---
if prompt := st.chat_input("您想了解哪項業務申請呢？"):
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 溫暖專業的 Persona 設定
        system_instruction = """
        你現在是「桃園市榮民服務處」的專業 AI 助理，名字叫「小助」。
        請根據提供的規範內容，用溫暖、耐心且清晰的方式回答。

        回覆原則：
        1. 語氣親切：稱呼對方為「您」，展現關懷。
        2. 排版分點：條理分明，讓民眾一眼看懂步驟。
        3. 誠實告知：規範未提到時，委婉引導聯繫榮服處，不亂編造。
        """
        
        full_p = f"{system_instruction}\n\n【參考規範內容】\n{context}\n\n【民眾問題】\n{prompt}"
        
        try:
            with st.spinner("小助正在翻閱規範，請稍候..."):
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
