import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import pdfplumber
import os

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="醫療輔具 AI 平台", page_icon="⚖️")
st.title("⚖️ 醫療輔具諮詢平台")
st.info("💡 歡迎使用！我是您的醫療輔具申請小助手。")

# --- 2. 側邊欄：動態掃描選單 ---
with st.sidebar:
    st.header("⚙️ 設定 AI 大腦")
    choice = st.selectbox("請選擇模型：", ["Gemini 3 Flash", "Gemma 3", "xAI Grok"])
    
    engine, m_id = "", ""
    if choice == "Gemini 3 Flash":
        engine, m_id = "GEMINI", "gemini-3-flash-preview"
    elif choice == "Gemma 3":
        engine, m_id = "GEMINI", "gemma-3-27b-it" 
    else:
        engine = "GROK"
        try:
            grok_client = OpenAI(api_key=st.secrets["XAI_API_KEY"], base_url="https://api.x.ai/v1")
            models_data = grok_client.models.list().data
            live_grok_models = [m.id for m in models_data]
            m_id = st.selectbox("👉 請選擇 Grok 型號：", live_grok_models) if live_grok_models else "grok-2"
        except: m_id = "grok-2"
    st.success(f"目前運行：{m_id}")

# --- 3. 讀取 PDF ---
PDF_PATH = "醫療輔具申請-作業程序.pdf"
@st.cache_resource
def get_pdf_text():
    if os.path.exists(PDF_PATH):
        with pdfplumber.open(PDF_PATH) as pdf:
            return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
    return ""
context = get_pdf_text()

# --- 4. 對話紀錄 ---
if "chat" not in st.session_state: st.session_state.chat = []
for m in st.session_state.chat:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. 核心：優化後的提詞策略 ---
if prompt := st.chat_input("您想了解哪項輔具申請呢？"):
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # 【優化重點】加入角色設定與回覆格式引導
        system_instruction = """
        你現在是「桃園市榮民服務處」的專業 AI 諮詢助理，名字叫「小助」。
        你的任務是根據提供的規範內容，用溫暖、耐心且清晰的方式回答民眾的問題。

        回覆原則：
        1. **語氣親切**：稱呼對方為「您」，適時加入「您好」、「別擔心」、「建議您」等溫馨語句。
        2. **排版分點**：如果涉及多個步驟或文件，請使用「1. 2. 3.」或「-」符號分列說明，讓長輩容易閱讀。
        3. **誠實告知**：若規範中完全沒有提到相關資訊，請委婉說明：「很抱歉，在目前的作業程序中沒有看到這項記載，建議您可以撥打榮服處電話 (03)XXX-XXXX 直接詢問承辦人，會最精準喔！」
        4. **禁止胡扯**：絕對不要編造規範以外的內容。
        """
        
        full_p = f"{system_instruction}\n\n【參考規範內容】\n{context}\n\n【民眾的問題】\n{prompt}"
        
        try:
            if engine == "GEMINI":
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                res = genai.GenerativeModel(m_id).generate_content(full_p)
                ans = res.text
            else:
                res = grok_client.chat.completions.create(model=m_id, messages=[{"role": "user", "content": full_p}])
                ans = res.choices[0].message.content

            st.markdown(ans)
            st.session_state.chat.append({"role": "assistant", "content": ans})
        except Exception as e:
            st.error(f"連線異常：{str(e)}")
