import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import pdfplumber
import os

# --- 1. 網頁設定 ---
st.set_page_config(page_title="醫療輔具 AI 雙平台", page_icon="⚖️")
st.title("⚖️ 醫療輔具諮詢 (三核心穩定版)")

# --- 2. 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 選擇 AI 大腦")
    choice = st.radio(
        "請選擇模型：",
        ["Gemini 3.1 Flash Lite (500次/天)", "Gemma 3 27B (1.4萬次/天)", "xAI Grok (付費穩定版)"]
    )
    
    if "Gemini 3.1" in choice:
        engine, m_id = "GEMINI", "gemini-3.1-flash-lite"
    elif "Gemma 3" in choice:
        engine, m_id = "GEMINI", "gemma-3-27b-it" 
    else:
        engine, m_id = "GROK", "grok-beta"

    st.success(f"目前鎖定：{m_id}")

# --- 3. 讀取 PDF ---
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

# --- 5. 發送問題 ---
if prompt := st.chat_input("請輸入問題..."):
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # 限制 PDF 字數，防止 Grok 因為內容太長而拒絕回答
        short_context = context[:8000] # 先抓前 8000 字測試
        full_p = f"請根據規範回答：\n{short_context}\n問題：{prompt}"
        
        try:
            if engine == "GEMINI":
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                res = genai.GenerativeModel(m_id).generate_content(full_p)
                ans = res.text
            else:
                # Grok 連線診斷
                client = OpenAI(api_key=st.secrets["XAI_API_KEY"], base_url="https://api.xai.com/v1")
                res = client.chat.completions.create(model=m_id, messages=[{"role": "user", "content": full_p}])
                
                if res and res.choices:
                    ans = res.choices[0].message.content
                else:
                    # 這行最重要，它會告訴我們 xAI 到底回傳了什麼垃圾
                    ans = f"⚠️ Grok 回傳內容異常。回傳物件：{str(res)}"

            st.markdown(ans)
            st.session_state.chat.append({"role": "assistant", "content": ans})
        except Exception as e:
            # 直接把死掉的報錯訊息噴在網頁上
            st.error(f"❌ {engine} 連線炸掉了！")
            st.warning(f"詳細錯誤訊息：{str(e)}")
