import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------
# 1. إعدادات الصفحة
# ---------------------------------------------------------
st.set_page_config(
    page_title="محلل الأسهم الإسلامية - البورصة المصرية",
    page_icon="🕌",
    layout="centered"
)

# ---------------------------------------------------------
# 2. التحديث الأوتوماتيكي (كل 60 ثانية)
# ---------------------------------------------------------
count = st_autorefresh(interval=60 * 1000, key="datarefreshcounter")

st.title("🕌 محلل كل الأسهم المتوافقة مع الشريعة")
st.caption(f"🔄 التحديث التلقائي مفعل (تحديث رقم: {count}) | تحليل شامل للأسهم الإسلامية في البورصة المصرية")

# ---------------------------------------------------------
# 3. إدخال مفتاح Gemini API
# ---------------------------------------------------------
api_key = st.sidebar.text_input("أدخل مفتاح Gemini API:", type="password")

# ---------------------------------------------------------
# 4. القائمة الموسعة للأسهم المتوافقة مع الشريعة الإسلامية
# ---------------------------------------------------------
ISLAMIC_STOCKS = [
    # أسهم مؤشر EGX33 الشريعة
    "COMI.CA", "AMOC.CA", "EKHO.CA", "ABUK.CA", "MFPC.CA",
    "ESRS.CA", "SWDY.CA", "ETEL.CA", "ORAS.CA", "HELI.CA",
    "TMGH.CA", "CICH.CA", "AUTO.CA", "ORWE.CA", "ISPH.CA",
    "JUFO.CA", "SKPC.CA", "DOMH.CA", "ALCN.CA", "EAST.CA",
    
    # أسهم إضافية متوافقة مع ضوابط الشريعة في البورصة المصرية
    "ADIB.CA", "EGAL.CA", "KABO.CA", "AMER.CA", "CCRS.CA",
    "OBRI.CA", "BINV.CA", "PHDC.CA", "RMDA.CA", "OCDI.CA",
    "CERA.CA", "DSCW.CA", "FWRY.CA", "RAYA.CA", "MCQE.CA"
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
    with st.spinner("⏳ جاري سحب وتحليل كافة الأسهم المتوافقة مع الشريعة والأخبار اللحظية..."):
        df_prices = fetch_live_prices(ISLAMIC_STOCKS)
        
        if df_prices.empty:
            st.error("تعذر جلب البيانات اللحظية، تأكد من اتصال الإنترنت أو وقت جلسة التداول.")
        else:
            st.subheader("📊 الأسعار اللحظية للأسهم الإسلامية")
            st.dataframe(df_prices, use_container_width=True)
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            أنت خبير ومحلل مالي متخصص في "الأسهم المتوافقة مع الشريعة الإسلامية في البورصة المصرية".
            أمامك البيانات السعرية اللحظية الحالية لجميع الأسهم الإسلامية المتاحة التي تم سحبها الآن:
            
            {df_prices.to_string(index=False)}
            
            قم بالبحث اللحظي عن أحدث الأخبار والتحليلات للأسهم المتوافقة مع الشريعة اليوم، وقدم تقريراً شاملاً يحتوي على:

            1. **جدول التوصيات والفرص اللحظية (للأسهم الإسلامية فقط):** 
               قم بعمل جدول شامل للأسهم التي بها فرص إيجابية، مع الأعمدة التالية بالترتيب:
               - **اسم الشركة باللغة العربية**
               - الرمز (Ticker)
               - السعر الحالي
               - سعر الشراء المقترح (نقطة الدخول)
               - سعر البيع المستهدف (الهدف الأول)
               - نسبة الصعود المتوقعة (%)
               - سعر إيقاف الخسارة (Stop Loss)

            2. **نظرة عامة على السيولة والاتجاه:** ملخص حركة السيولة الموجهة للأسهم الإسلامية في السوق اليوم.
            3. **تأثير الأخبار اللحظية:** أهم الأخبار والقرارات المؤثرة على الشركات الإسلامية اليوم.
            4. **أسهم تحت المراقبة / تحذيرات:** الأسهم التي تعاني من ضعف سيولة أو ضغط بيعي.
            5. **توصية تنفيذية سريعة للمستثمر.**

            اكتب التقرير بأسلوب مالي احترافي ودقيق.
            """
            
            response = model.generate_content(prompt)
            
            st.markdown("---")
            st.subheader("💡 التقرير التحليلي الشامل للأسهم الإسلامية")
            st.markdown(response.text)
