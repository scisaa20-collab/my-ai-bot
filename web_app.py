import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import pdfplumber
import os

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="醫療輔具 AI 平台", page_icon="⚖️")
st.title("⚖️ 醫療輔具諮詢 (雙擎最終版)")

# --- 2. 側邊欄：動態抓取真實型號 ---
with st.sidebar:
    st.header("⚙️ 選擇 AI 大腦")
    engine_choice = st.radio("請選擇平台：", ["xAI Grok (穩定版)", "Google Gemini (動態掃描)"])
    
    engine = ""
    m_id = ""
    
    if engine_choice == "xAI Grok (穩定版)":
        engine = "GROK"
        grok_client = OpenAI(api_key=st.secrets["XAI_API_KEY"], base_url="https://api.x.ai/v1")
        try:
            valid_models = [m.id for m in grok_client.models.list().data if "grok" in m.id]
            m_id = valid_models[0] if valid_models else "grok-beta"
        except:
            m_id = "grok-beta"
        st.success(f"目前連線：{m_id}")
        
    else:
        # Gemini 真實清單掃描
        engine = "GEMINI"
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            # 照妖鏡：直接抓取支援聊天的所有真實 ID
            live_models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            if live_models:
                # 讓使用者從真正活著的名單裡挑選
                m_id = st.selectbox("請選擇真實可用的 Gemini 型號：", live_models)
                st.success(f"目前連線：{m_id}")
            else:
                st.error("❌ 這把金鑰找不到任何支援聊天的模型")
        except Exception as e:
            st.error(f"❌ 讀取 Gemini 清單失敗：{e}")

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
if prompt := st.chat_input("請輸入輔具申請相關問題..."):
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        full_p = f"請根據規範精準回答，未提到請告知：\n\n{context}\n\n問題：{prompt}"
        try:
            if engine == "GEMINI":
                # 使用你從選單挑出的真實 ID
                res = genai.GenerativeModel(m_id).generate_content(full_p)
                ans = res.text
            else:
                # Grok 連線
                res = grok_client.chat.completions.create(
                    model=m_id, 
                    messages=[{"role": "user", "content": full_p}]
                )
                ans = res.choices[0].message.content

            st.markdown(ans)
            st.session_state.chat.append({"role": "assistant", "content": ans})
        except Exception as e:
            st.error(f"❌ {engine} 連線失敗：{str(e)}")
