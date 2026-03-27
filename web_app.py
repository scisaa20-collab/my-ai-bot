import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import pdfplumber
import os

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="榮民業務智慧導航", page_icon="🏛️")

# --- 2. 視覺美化：隱藏右下角皇冠與上方雜物 ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("🏛️ 榮民服務智慧諮詢助理")
st.info("💡 您好！我是您的業務小助手「小助」，目前預設使用 Gemma 3 為您服務。")

# --- 3. 側邊欄：模型設定與自動偵測 ---
with st.sidebar:
    st.header("⚙️ 系統設定")
    # 將 Gemma 3 移到清單第一個，作為預設選項
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
        system_instruction = """
        你現在是「桃園市榮民服務處」的專業 AI 助理，名字叫「小助」。
        請根據提供的規範內容，用溫暖、耐心且清晰的方式回答。

        回覆原則：
        1. 語氣親切：稱呼對方為「您」，多用些溫馨禮貌的詞語。
        2. 排版分點：使用「1. 2. 3.」或「-」符號。
        3. 誠實告知：若規範沒提到，請委婉說「目前規範未記載，建議撥打榮服處電話詢問」。
        4. 禁止胡扯：絕對不編造規範外的資訊。
        """
        
        full_p = f"{system_instruction}\n\n【參考規範內容】\n{context}\n\n【民眾問題】\n{prompt}"
        
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
