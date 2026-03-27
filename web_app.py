import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import pdfplumber
import os

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="醫療輔具雙引擎助理", page_icon="🤖")
st.title("🤖 醫療輔具 AI 諮詢平台")
st.info("💡 系統已連線：桃園市榮民服務處《醫療輔具申請作業程序》")

# --- 2. 側邊欄設定 (雙引擎與自動診斷) ---
with st.sidebar:
    st.header("⚙️ AI 引擎切換")
    engine = st.radio("當前使用大腦：", ["Google Gemini", "xAI Grok"])
    
    if engine == "Google Gemini":
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            # 【方案一】自動偵測清單，避免 404
            all_models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # 優先找 3.1 或 1.5 系列
            gemini_models = [m for m in all_models if "gemini" in m]
            selected_model = st.selectbox("Gemini 型號選擇：", gemini_models)
            st.success("✅ Gemini 已就緒")
        except Exception as e:
            st.error(f"Gemini 初始化失敗：{e}")
    else:
        # Grok 設定 (方案二)
        selected_model = "grok-beta" 
        grok_client = OpenAI(
            api_key=st.secrets["XAI_API_KEY"],
            base_url="https://api.xai.com/v1",
        )
        st.success("✅ Grok 引擎已啟動")

# --- 3. 讀取 PDF 內容 ---
PDF_PATH = "醫療輔具申請-作業程序.pdf"
@st.cache_resource
def load_pdf_content():
    if os.path.exists(PDF_PATH):
        try:
            with pdfplumber.open(PDF_PATH) as pdf:
                return "\n".join([(p.extract_text() or "") for p in pdf.pages])
        except: return None
    return None

knowledge_context = load_pdf_content()

# --- 4. 對話紀錄 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. 處理提問 ---
if prompt := st.chat_input("請輸入輔具申請相關問題..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not knowledge_context:
            st.error("❌ 找不到 PDF 規範檔案，請確認檔案已上傳。")
        else:
            full_prompt = f"請根據以下規範精準回答問題，若未提到請告知：\n\n{knowledge_context}\n\n問題：{prompt}"
            try:
                if engine == "Google Gemini":
                    model = genai.GenerativeModel(selected_model)
                    response = model.generate_content(full_prompt)
                    answer = response.text
                else:
                    # 使用 Grok 引擎
                    response = grok_client.chat.completions.create(
                        model=selected_model,
                        messages=[{"role": "user", "content": full_prompt}]
                    )
                    answer = response.choices[0].message.content
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                st.error(f"❌ {engine} 連線異常")
                st.code(f"錯誤詳情：{e}")
                if "429" in str(e):
                    st.warning("💡 這個大腦今天累了（額度滿了），請從左側切換到另一個大腦試試！")
