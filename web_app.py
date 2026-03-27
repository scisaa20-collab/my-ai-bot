import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import pdfplumber
import os

# --- 1. 網頁設定 ---
st.set_page_config(page_title="醫療輔具 AI 雙平台", page_icon="⚖️")
st.title("⚖️ 醫療輔具諮詢 (穩定三核心)")

# --- 2. 側邊欄：只留你表上「真的有額度」的這 3 個 ---
with st.sidebar:
    st.header("⚙️ 選擇 AI 大腦")
    choice = st.radio(
        "請選擇模型：",
        ["Gemini 3.1 Flash Lite", "Gemma 3 27B", "xAI Grok"]
    )
    
    # 根據你的額度表精準鎖定 ID
    if "Gemini 3.1" in choice:
        engine, m_id = "GEMINI", "gemini-3.1-flash-lite"
    elif "Gemma 3" in choice:
        engine, m_id = "GEMINI", "gemma-3-27b-it" 
    else:
        # 修正後的 Grok 官方網址與 ID
        engine, m_id = "GROK", "grok-4.1-fast" # 或是用 grok-beta
        grok_client = OpenAI(
            api_key=st.secrets["XAI_API_KEY"],
            base_url="https://api.x.ai/v1" # <--- 修正這行！不是 xai.com
        )

    st.success(f"目前鎖定：{m_id}")

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
        full_p = f"請根據規範回答：\n{context}\n問題：{prompt}"
        try:
            if engine == "GEMINI":
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                res = genai.GenerativeModel(m_id).generate_content(full_p)
                ans = res.text
            else:
                # Grok 正式發送請求
                res = grok_client.chat.completions.create(
                    model=m_id, 
                    messages=[{"role": "user", "content": full_p}]
                )
                ans = res.choices[0].message.content

            st.markdown(ans)
            st.session_state.chat.append({"role": "assistant", "content": ans})
        except Exception as e:
            st.error(f"❌ {engine} 連線失敗：{str(e)}")
