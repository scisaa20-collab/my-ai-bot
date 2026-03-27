import streamlit as st
import google.generativeai as genai
import pdfplumber
import os

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="醫療輔具 AI 助理", page_icon="🤖")
st.title("🤖 醫療輔具申請諮詢助手")
st.caption("本系統根據《醫療輔具申請作業程序》提供諮詢")

# --- 2. API 設定與模型挑選 ---
# 從 Streamlit Secrets 讀取你的金鑰
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# 直接鎖定你清單中額度最高的模型 (每天 500 次)
# 這樣就不會再出現 429 額度爆掉的問題了
MODEL_NAME = 'gemini-3.1-flash-lite'
model = genai.GenerativeModel(MODEL_NAME)

# --- 3. 讀取 PDF 內容 ---
@st.cache_resource
def load_pdf_content():
    path = "醫療輔具申請-作業程序.pdf"
    all_text = ""
    if os.path.exists(path):
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: all_text += text + "\n"
            return all_text
        except:
            return None
    return None

knowledge_context = load_pdf_content()

# --- 4. 對話介面與紀錄 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# 顯示歷史訊息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 處理新提問
if prompt := st.chat_input("請問想了解哪種輔具的申請規則？"):
    # 紀錄使用者問題
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 生成 AI 回覆
    with st.chat_message("assistant"):
        if not knowledge_context:
            response_text = "❌ 系統錯誤：找不到 PDF 規範檔案，請確認檔案已上傳至 GitHub。"
        else:
            # 建立完整的提示詞
            full_prompt = f"請根據以下規範回答問題，若規範未提到請告知：\n\n{knowledge_context}\n\n問題：{prompt}"
            try:
                ai_response = model.generate_content(full_prompt)
                response_text = ai_response.text
            except Exception as e:
                response_text = f"❌ AI 連線出錯：請檢查 API 金鑰或稍後再試。({e})"
        
        st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
