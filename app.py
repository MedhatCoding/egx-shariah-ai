import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------
# 1. إعدادات الصفحة
# ---------------------------------------------------------
st.set_page_config(
    page_title="محلل مؤشر الشريعة EGX33 اللحظي",
    page_icon="📈",
    layout="centered"
)

# ---------------------------------------------------------
# 2. التحديث الأوتوماتيكي (كل 60 ثانية)
# ---------------------------------------------------------
count = st_autorefresh(interval=60 * 1000, key="datarefreshcounter")

st.title("📈 محلل مؤشر الشريعة (EGX33) اللحظي")
st.caption(f"🔄 التحديث التلقائي مفعل (تحديث رقم: {count}) | يحلل الأسعار والأخبار اللحظية")

# ---------------------------------------------------------
# 3. إدخال مفتاح Gemini API
# ---------------------------------------------------------
api_key = st.sidebar.text_input("أدخل مفتاح Gemini API:", type="password")

# ---------------------------------------------------------
# 4. قائمة أسهم مؤشر الشريعة (EGX33)
# ---------------------------------------------------------
SHARIAH_STOCKS = [
    "COMI.CA", "AMOC.CA", "EKHO.CA", "ABUK.CA", "MFPC.CA",
    "ESRS.CA", "SWDY.CA", "ETEL.CA", "ORAS.CA", "HELI.CA",
    "TMGH.CA", "CICH.CA", "AUTO.CA", "ORWE.CA", "ISPH.CA"
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
# 6. التشغيل والتحليل التلقائي
# ---------------------------------------------------------
if not api_key:
    st.warning("⚠️ برجاء إدخال مفتاح Gemini API في الشريط الجانبي لبدء الجلب والتحليل أوتوماتيكياً.")
else:
    with st.spinner("⏳ جاري سحب الأسعار والأخبار اللحظية وتحليلها بواسطة الذكاء الاصطناعي..."):
        df_prices = fetch_live_prices(SHARIAH_STOCKS)
        
        if df_prices.empty:
            st.error("تعذر جلب البيانات اللحظية، تأكد من اتصال الإنترنت أو وقت جلسة التداول.")
        else:
            st.subheader("📊 الأسعار اللحظية الحالية")
            st.dataframe(df_prices, use_container_width=True)
            
            # ضبط إعدادات Gemini مع خاصية البحث عن الأخبار
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            أنت محلل مالي وخبير استثماري محترف في البورصة المصرية متكفّل بـ مؤشر الشريعة (EGX33).
            أمامك البيانات السعرية اللحظية الحالية التي تم سحبها من السوق الآن:
            
            {df_prices.to_string(index=False)}
            
            قم بالبحث اللحظي عن أحدث الأخبار الاقتصادية المؤثرة على البورصة المصرية وهذه الشركات اليوم، ثم قدم تقريراً شاملاً يحتوي على:
            
            1. **جدول التوصيات والفرص اللحظية:** 
               قم بعمل جدول يحتوي على الأسهم الموصى بها، ويتضمن الأعمدة التالية بالترتيب:
               - **اسم الشركة باللغة العربية** (مثال: البنك التجاري الدولي، مصر للألومنيوم، طلعت مصطفى، مصر للجديدة للأسكان، إلخ)
               - الرمز (Ticker)
               - السعر الحالي
               - سعر الشراء المقترح (نقطة الدخول)
               - سعر البيع المستهدف (الهدف الأول)
               - نسبة الصعود المتوقعة (%)
               - سعر إيقاف الخسارة (Stop Loss)

            2. **نظرة عامة على السيولة والاتجاه:** تحليل حركة السوق والاتجاه العام.
            3. **تأثير الأخبار اللحظية:** ملخص لأهم الأخبار الاقتصادية أو القرارات المؤثرة على أسهم مؤشر الشريعة اليوم.
            4. **أسهم تحت المراقبة / تحذيرات:** الأسهم التي بها مخاطرة عالية أو ضغط بيعي.
            5. **توصية تنفيذية سريعة للمستثمر.**
            
            اكتب التقرير بأسلوب مالي احترافي ودقيق جداً.
            """
            
            # تشغيل التوليد وتحديث التقرير
            response = model.generate_content(prompt)
            
            st.markdown("---")
            st.subheader("💡 التقرير التحليلي الشامل (أسعار + أخبار لحظية)")
            st.markdown(response.text)
            
