import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------
# 1. إعدادات الصفحة
# ---------------------------------------------------------
st.set_page_config(
    page_title="محلل مؤشر الشريعة EGX33",
    page_icon="🕌",
    layout="centered"
)

# ---------------------------------------------------------
# 2. التحديث الأوتوماتيكي (كل 60 ثانية)
# ---------------------------------------------------------
count = st_autorefresh(interval=60 * 1000, key="datarefreshcounter")

st.title("🕌 محلل مؤشر الشريعة (EGX33) حصرياً")
st.caption(f"🔄 التحديث التلقائي مفعل (تحديث رقم: {count}) | تحليل خاص فقط بأسهم الشريعة")

# ---------------------------------------------------------
# 3. إدخال مفتاح Gemini API
# ---------------------------------------------------------
api_key = st.sidebar.text_input("أدخل مفتاح Gemini API:", type="password")

# ---------------------------------------------------------
# 4. قائمة أسهم مؤشر الشريعة المعتمدة (EGX33)
# ---------------------------------------------------------
SHARIAH_STOCKS = [
    "COMI.CA", "AMOC.CA", "EKHO.CA", "ABUK.CA", "MFPC.CA",
    "ESRS.CA", "SWDY.CA", "ETEL.CA", "ORAS.CA", "HELI.CA",
    "TMGH.CA", "CICH.CA", "AUTO.CA", "ORWE.CA", "ISPH.CA",
    "JUFO.CA", "SKPC.CA", "DOMH.CA", "ALCN.CA", "EAST.CA"
]

# ---------------------------------------------------------
# 5. دالة جلب الأسعار اللحظية أوتوماتيكياً
# ---------------------------------------------------------
@st.cache_data(ttl=30)
def fetch_live_prices(tickers):
    data_list = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            if not hist.empty:
                last_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else last_price
                change_percent = ((last_price - prev_price) / prev_price) * 100
                volume = hist['Volume'].iloc[-1]
                
                data_list.append({
                    "الرمز": ticker.replace(".CA", ""),
                    "السعر الحالي": round(last_price, 2),
                    "التغير %": round(change_percent, 2),
                    "حجم التداول": volume
                })
        except Exception:
            continue
    return pd.DataFrame(data_list)

# ---------------------------------------------------------
# 6. التشغيل والتحليل التلقائي الحصري لمؤشر الشريعة
# ---------------------------------------------------------
if not api_key:
    st.warning("⚠️ برجاء إدخال مفتاح Gemini API في الشريط الجانبي لبدء الجلب والتحليل أوتوماتيكياً.")
else:
    with st.spinner("⏳ جاري تحليل أسهم ومؤشر الشريعة EGX33 حصرياً..."):
        df_prices = fetch_live_prices(SHARIAH_STOCKS)
        
        if df_prices.empty:
            st.error("تعذر جلب البيانات اللحظية، تأكد من اتصال الإنترنت أو وقت جلسة التداول.")
        else:
            st.subheader("📊 الأسعار اللحظية لأسهم مؤشر الشريعة (EGX33)")
            st.dataframe(df_prices, use_container_width=True)
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            تنبيه هام: أنت خبير متخصص حصرياً في "مؤشر الشريعة بالبورصة المصرية (EGX33)". 
            كل تحليلاتك وتوصياتك وأخبارك يجب أن تقتصر فقط وحصرياً على الأسهم المتوافقة مع الشريعة الإسلامية والمدرجة ضمن مؤشر EGX33. يمنع منعاً باتاً التطرق لأي سهم خارج هذا المؤشر.

            أمامك البيانات السعرية اللحظية الحالية لأسهم الشريعة التي تم سحبها الآن:
            {df_prices.to_string(index=False)}

            قم بالبحث اللحظي عن أداء "مؤشر الشريعة EGX33" والأخبار الخاصة بأسهمه اليوم، ثم قدم التقرير بالترتيب التالي:

            1. **تحليل أداء مؤشر الشريعة EGX33:**
               - الاتجاه العام للمؤشر (صاعد / هابط / عرضي).
               - نقاط الدعم والمقاومة الرئيسية للمؤشر.
               - حجم السيولة الموجهة لأسهم الشريعة.

            2. **جدول التوصيات والفرص اللحظية (لأسهم الشريعة فقط):**
               جدول يحتوي على الأسهم الموصى بها فقط مع الأعمدة التالية:
               - **اسم الشركة بالعربي** (مثال: طلعت مصطفى، البنك التجاري الدولي، إلخ)
               - الرمز (Ticker)
               - السعر الحالي
               - سعر الشراء المقترح (نقطة الدخول)
               - سعر البيع المستهدف (الهدف الأول)
               - نسبة الصعود المتوقعة (%)
               - سعر إيقاف الخسارة (Stop Loss)

            3. **أخبار أسهم الشريعة اللحظية:** ملخص لأهم الأخبار والنتائج الخاصة بشركات مؤشر EGX33 اليوم.
            4. **تنبيهات ومخاطر:** أسهم الشريعة التي تعاني من ضغط بيعي أو ضعف في السيولة.
            5. **توصية تنفيذية سريعة للمستثمر.**

            التزم بأسلوب مالي احترافي ودقيق جداً.
            """
            
            response = model.generate-content(prompt) if hasattr(model, 'generate-content') else model.generate_content(prompt)
            
            st.markdown("---")
            st.subheader("💡 التقرير التحليلي الحصري لمؤشر الشريعة (EGX33)")
            st.markdown(response.text)
