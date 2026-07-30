import streamlit as st
import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from google import genai

# ---------------------------------------------------------
# 1. إعدادات الصفحة والتصميم
# ---------------------------------------------------------
st.set_page_config(
    page_title="منصة الأسهم الإسلامية | EGX Shariah",
    page_icon="🕌",
    layout="wide"
)

st.title("🕌 منصة تحليل الأسهم الإسلامية (EGX Shariah)")
st.caption("متابعة لحظية ومحلل ذكي لأهم الأسهم المعتمدة شرعياً بالبورصة المصرية")

# ---------------------------------------------------------
# 2. مفتاح API
# ---------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("🔑 أدخل مفتاح Gemini API الخاص بك:", type="password")

# ---------------------------------------------------------
# 3. قائمة الأسهم الإسلامية المعتمدة
# ---------------------------------------------------------
ISLAMIC_STOCKS_MAP = {
    "ADIB.CA": "مصرف أبوظبي الإسلامي",
    "SAUD.CA": "بنك البركة مصر",
    "FAIT.CA": "بنك فيصل الإسلامي",
    "AMOC.CA": "أموك للزيوت",
    "ABUK.CA": "أبوقير للأسمدة",
    "MFPC.CA": "موبكو للأسمدة",
    "SKPC.CA": "سيدي كرير للبتروكيماويات",
    "TMGH.CA": "مجموعة طلعت مصطفى",
    "HELI.CA": "مصر الجديدة للإسكان",
    "MASR.CA": "مدينة مصر للإسكان",
    "PHDC.CA": "بالم هيلز للتعمير",
    "SWDY.CA": "السويدي إليكتريك",
    "ESRS.CA": "حديد عز",
    "ETEL.CA": "المصرية للاتصالات",
    "FWRY.CA": "فوري للمدفوعات",
    "ISPH.CA": "ابن سينا فارما",
    "RMDA.CA": "رميدا للأدوية",
    "SPMD.CA": "سبيد ميديكال"
}

# ---------------------------------------------------------
# 4. جلب أسعار الأسهم
# ---------------------------------------------------------
def get_stock_data(ticker, name):
    try:
        data = yf.Ticker(ticker).history(period="5d")
        if not data.empty and len(data) >= 1:
            last_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2] if len(data) > 1 else last_price
            change_pct = ((last_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
            vol = data['Volume'].iloc[-1]
            return {
                "الشركة": name,
                "الرمز": ticker.replace(".CA", ""),
                "السعر (ج.م)": round(last_price, 2),
                "التغير %": round(change_pct, 2),
                "حجم التداول": int(vol)
            }
    except Exception:
        pass
    return None

def fetch_all_data():
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_stock_data, t, n) for t, n in ISLAMIC_STOCKS_MAP.items()]
        for f in futures:
            res = f.result()
            if res:
                results.append(res)
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by="حجم التداول", ascending=False)
    return df

# ---------------------------------------------------------
# 5. زر التحديث وجدول الأسعار
# ---------------------------------------------------------
if st.button("🔄 تحديث الأسعار الآن"):
    st.session_state['df_data'] = fetch_all_data()

if 'df_data' not in st.session_state:
    st.session_state['df_data'] = fetch_all_data()

df = st.session_state['df_data']

if df.empty:
    st.error("⚠️ فشل جلب البيانات، اضغط تحديث للتحقق مرة أخرى.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")

# ---------------------------------------------------------
# 6. قسم التقرير والذكاء الاصطناعي
# ---------------------------------------------------------
if st.button("✨ استخراج التقرير والتحليل الذكي"):
    if not api_key:
        st.warning("⚠️ يرجى أدخال مفتاح GEMINI_API_KEY أولاً.")
    elif df.empty:
        st.error("لا توجد بيانات أسهم لتحليلها.")
    else:
        with st.spinner("🧠 جاري إعداد التقرير بواسطة الذكاء الاصطناعي..."):
            try:
                # تشغيل عميل الذكاء الاصطناعي الجديد
                client = genai.Client(api_key=api_key)
                
                # إعداد البيانات المقترحة للتحليل
                table_text = df.to_string(index=False)
                
                prompt = f"""
                أنت محلل مالي خبير ومستشار استثماري للأسهم المتوافقة مع الشريعة في البورصة المصرية.
                إليك البيانات الحالية للأسهم:

                {table_text}

                المطلوب:
                1. جدول بأفضل الفرص الشرائية (الشركة، الرمز، السعر الحالي، المستهدف، وقف الخسارة).
                2. رؤية سريعة وحالة السوق وحركة السيولة.
                """

                # طلب التحليل بموديل flash المباشر
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )

                st.session_state['report_text'] = response.text
                st.rerun()

            except Exception as err:
                st.error(f"حدث خطأ أثناء طلب التقرير: {err}")

# عرض التقرير الناتج
if 'report_text' in st.session_state:
    st.success("تم التقرير بنجاح! 🎯")
    st.markdown(st.session_state['report_text'])
    
