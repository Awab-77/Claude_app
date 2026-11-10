import streamlit as st
import anthropic
import pypdf

# إعدادات الصفحة
st.set_page_config(page_title="Claude AI", page_icon="🤖", layout="wide")

# جلب المفاتيح من الإعدادات السرية (مع وضع "admin" كقيمة افتراضية)
api_key = st.secrets.get("ANTHROPIC_API_KEY", "admin")
base_url = st.secrets.get("ANTHROPIC_BASE_URL", "https://api.openapis.online/anthropic")

@st.cache_resource
def get_client():
    return anthropic.Anthropic(api_key=api_key, base_url=base_url, timeout=60.0)

client = get_client()

st.title("🤖 Claude - دردشة ورفع ملفات")

# الشريط الجانبي
with st.sidebar:
    st.header("⚙️ الإعدادات")
    model = st.selectbox("اختر النموذج:", ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"])
    
    st.markdown("---")
    st.header("📄 رفع مستند")
    uploaded_file = st.file_uploader("ارفع ملف PDF أو TXT", type=["pdf", "txt"])
    
    if uploaded_file:
        if uploaded_file.name.endswith(".pdf"):
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = "\n".join([page.extract_text() for page in pdf_reader.pages])
            st.session_state.file_text = text
            st.success("تمت قراءة الـ PDF بنجاح!")
        else:
            st.session_state.file_text = uploaded_file.read().decode("utf-8")
            st.success("تمت قراءة الملف النصي بنجاح!")
            
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.messages = []
        st.session_state.file_text = ""
        st.rerun()

# تهيئة الذاكرة
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_text" not in st.session_state:
    st.session_state.file_text = ""

# عرض الرسائل السابقة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# مربع الدردشة
if prompt := st.chat_input("اكتب سؤالك هنا..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("🤔 Claude يفكر..."):
                # تجهيز الرسائل للإرسال
                api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                
                # إذا تم رفع ملف، ندمجه مع السؤال الحالي
                if st.session_state.file_text:
                    last_msg = api_messages[-1]["content"]
                    api_messages[-1]["content"] = f"إليك محتوى المستند المرفق:\n{st.session_state.file_text}\n\nبناءً على هذا المستند، أجب على سؤالي:\n{last_msg}"

                response = client.messages.create(
                    model=model,
                    max_tokens=4096,
                    messages=api_messages
                )
                reply = response.content[0].text
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.error(f"حدث خطأ: {str(e)}")
