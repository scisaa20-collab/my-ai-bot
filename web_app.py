import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import pdfplumber
import os

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="醫療輔具 AI 平台", page_icon="⚖️")
st.title("⚖️ 醫療輔具諮詢平台")
st.info("💡 系統已連線：桃園市榮民服務處作業程序")

# --- 2. 側邊欄：恢復之前測試可行的版本 ---
with st.sidebar:
    st.header("⚙️ 選擇 AI 大腦")
    # 乾淨的下拉選單
    choice = st.selectbox(
        "請選擇模型：",
        ["Gemini 3 Flash", "Gemma 3", "xAI Grok"]
    )
    
    if choice == "Gemini 3 Flash":
        engine, m_id = "GEMINI", "gemini-3-flash-preview"
    elif choice == "Gemma 3":
        engine, m_id = "GEMINI", "gemma-3-27b-it" 
    else:
        # 回歸之前測試成功的 grok-beta 版本
        engine, m_id = "GROK", "grok-beta"
        grok_client = OpenAI(
            api_key=st.secrets["XAI_API_KEY"],
            base_url="https://api.x.ai/v1"
        )
    
    st.success(f"目前運行：{m_id}")

# --- 3. 讀取 PDF 文字 ---
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

# --- 4. 對話紀錄 ---
if "chat" not in st.session_state: st.session_state.chat = []
for m in st.session_state.chat:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. 發送提問 ---
if prompt := st.chat_input("請輸入問題..."):
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        full_p = f"請根據規範精準回答，未提到請告知：\n\n{context}\n\n問題：{prompt}"
        try:
            if engine == "GEMINI":
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                res = genai.GenerativeModel(m_id).generate_content(full_p)
                ans = res.text
            else:
                # Grok 正式連線 (恢復 grok-beta)
                res = grok_client.chat.completions.create(
                    model=m_id, 
                    messages=[{"role": "user", "content": full_p}]
                )
                ans = res.choices[0].message.content

            st.markdown(ans)
            st.session_state.chat.append({"role": "assistant", "content": ans})
        except Exception as e:
            st.error(f"❌ {engine} 連線失敗：{str(e)}")
