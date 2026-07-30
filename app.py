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
# 2. التحديث الأوتوماتيكي (كل 60 ثانية - دقيقة واحدة)
# ---------------------------------------------------------
# الكود ده بيخلي الصفحة تعيد تحميل نفسها أوتوماتيكياً كل 60000 مللي ثانية (دقيقة)
count = st_autorefresh(interval=60 * 1000, key="datarefreshcounter")

st.title("📈 محلل مؤشر الشريعة (EGX33) اللحظي التلقائي")
st.caption(f"🔄 التحديث التلقائي مفعل (تحديث رقم: {count}) | يعمل في الخلفية")

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
@st.cache_data(ttl=30)  # جلب بيانات جديدة كل 30 ثانية
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
                    "السهم": ticker.replace(".CA", ""),
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
    st.warning("⚠️ برجاء إدخال مفتاح Gemini API في الشريط الجانبي لبدء جلب وتحليل البيانات أوتوماتيكياً.")
else:
    with st.spinner("⏳ جاري سحب الأسعار وتحليلها أوتوماتيكياً..."):
        # أ. سحب الأسعار
        df_prices = fetch_live_prices(SHARIAH_STOCKS)
        
        if df_prices.empty:
            st.error("تعذر جلب البيانات اللحظية، تأكد من اتصال الإنترنت أو وقت جلسة التداول (البورصة مغلقة حالياً).")
        else:
            # عرض جدول الأسعار اللحظية
            st.subheader("📊 الأسعار اللحظية الحالية")
            st.dataframe(df_prices, use_container_width=True)
            
            # ب. إرسال البيانات للذكاء الاصطناعي للتحليل
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            أنت محلل مالي وخبير استثماري محترف في البورصة المصرية متكفّل بـ مؤشر الشريعة (EGX33).
            أمامك البيانات السعرية اللحظية الحالية التي تم سحبها من السوق الآن:
            
            {df_prices.to_string(index=False)}
            
            قم بتقديم تقرير تحليلي مرن واحترافي موجه لمستثمر فرد، يحتوي على:
            1. **نظرة عامة على السيولة والاتجاه:** هل الاتجاه العام صاعد، هابط، أم عرضي؟
            2. **أفضل الفرص اللحظية (شراء/مضاربة):** حدد 2 إلى 3 أسهم تُظهر إيجابية بناءً على الحركة وحجم التداول.
            3. **أسهم تحت المراقبة / إيقاف خسارة:** حدد الأسهم التي تشهد ضغط بيعي أو تراجع.
            4. **توصية تنفيذية سريعة:** خطة عمل للمستثمر للجلسة الحالية.
            
            اكتب التقرير بأسلوب مالي محترف، واضح، ومباشر دون مقدمات طويلة.
            """
            
            response = model.generate_content(prompt)
            
            # ج. عرض التقرير اللحظي
            st.markdown("---")
            st.subheader("💡 التقرير التحليلي اللحظي (يتحدث تلقائياً)")
            st.markdown(response.text)
      
