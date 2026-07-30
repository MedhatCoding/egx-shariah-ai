import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------
# 1. إعدادات الصفحة والتنسيق البصري الاحترافي (CSS Customization)
# ---------------------------------------------------------
st.set_page_config(
    page_title="محلل الأسهم الإسلامية | EGX Shariah",
    page_icon="🕌",
    layout="centered"
)

# إضافة لمسات تصميم احترافية
st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
        font-size: 16px;
        background-color: #0d6efd;
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #0b5ed7;
        box-shadow: 0 4px 12px rgba(13, 110, 253, 0.3);
    }
    div[data-testid="stMetricValue"] {
        font-size: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. التحديث الأوتوماتيكي للأسعار فقط (كل 60 ثانية)
# ---------------------------------------------------------
count = st_autorefresh(interval=60 * 1000, key="datarefreshcounter")

# الهيدر الرئيسي بتصميم أنيق
st.title("🕌 منصة تحليل الأسهم الإسلامية")
st.caption("تتبع تحليلي للأسهم المصرية المعتمدة شرعياً وفق معايير الأزهر الشريف و AAOIFI")

# ---------------------------------------------------------
# 3. جلب مفتاح Gemini API أوتوماتيكياً من Secrets
# ---------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input("🔑 أدخل مفتاح Gemini API:", type="password")

# ---------------------------------------------------------
# 4. القائمة الشاملة للأسهم المتوافقة مع الشريعة
# ---------------------------------------------------------
VERIFIED_ISLAMIC_STOCKS = [
    # قطاع البنوك والخدمات المالية الإسلامية
    "ADIB.CA", "SAUD.CA",
    # قطاع البتروكيماويات والأسمدة والغاز
    "AMOC.CA", "ABUK.CA", "MFPC.CA", "SKPC.CA", "KABO.CA",
    # قطاع العقارات والتطوير العمراني
    "TMGH.CA", "HELI.CA", "ORAS.CA", "PHDC.CA", "OCDI.CA", "AMER.CA",
    # قطاع الصناعة والتصنيع والأغذية
    "SWDY.CA", "ESRS.CA", "JUFO.CA", "DOMH.CA", "ORWE.CA", "ALCN.CA", "EGAL.CA", "MCQE.CA",
    # قطاع الاتصالات، التكنولوجيا والأدوية
    "ETEL.CA", "ISPH.CA", "RMDA.CA", "FWRY.CA", "RAYA.CA"
]

# ---------------------------------------------------------
# 5. دالة جلب الأسعار اللحظية
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
                    "السعر الحالي (ج.م)": round(last_price, 2),
                    "التغير %": round(change_percent, 2),
                    "حجم التداول": volume
                })
        except Exception:
            continue
    return pd.DataFrame(data_list)

# ---------------------------------------------------------
# 6. عرض البيانات والبطاقات
# ---------------------------------------------------------
df_prices = fetch_live_prices(VERIFIED_ISLAMIC_STOCKS)

if df_prices.empty:
    st.error("⚠️ تعذر جلب البيانات اللحظية، تأكد من اتصال الإنترنت أو وقت جلسة التداول.")
else:
    # عرض إحصائيات سريعة في الأعلى
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="عدد الأسهم المتابعة", value=f"{len(df_prices)} سهم")
    with col2:
        st.metric(label="حالة التحديث", value=f"تحديث #{count}", delta="نشط (60ث)")

    st.markdown("---")
    st.subheader("📊 جدول الأسعار اللحظية")
    
    # عرض جدول الأسعار بتنسيق متجاوب
    st.dataframe(
        df_prices, 
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # ---------------------------------------------------------
    # 7. زر التحليل الذكي
    # ---------------------------------------------------------
    if st.button("✨ استخراج التقرير والتحليل الذكي للأسهم"):
        if not api_key:
            st.warning("⚠️ لم يتم العثور على مفتاح API. برجاء إضافته في Secrets أو إدخاله في الشريط الجانبي.")
        else:
            with st.spinner("🧠 جاري تحليل الاتجاهات وصياغة التوصيات..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    prompt = f"""
                    أنت خبير ومحلل مالي متخصص حصرياً في "الأسهم المتوافقة مع الشريعة الإسلامية بالبورصة المصرية".
                    أمامك البيانات السعرية اللحظية لأسهم الشركات المعتمدة شرعياً فقط والمتاحة الآن:
                    
                    {df_prices.to_string(index=False)}
                    
                    قدم تقريراً تحليلياً شاملاً بالترتيب التالي:

                    1. **جدول التوصيات والفرص اللحظية:** 
                       جدول منظّم للأسهم التي بها فرص إيجابية بالترتيب:
                       - **اسم الشركة باللغة العربية**
                       - الرمز (Ticker)
                       - السعر الحالي
                       - سعر الشراء المقترح (نقطة الدخول)
                       - سعر البيع المستهدف (الهدف الأول)
                       - نسبة الصعود المتوقعة (%)
                       - سعر إيقاف الخسارة (Stop Loss)

                    2. **نظرة عامة على السيولة والاتجاه:** ملخص حركات السيولة الموجهة للقطاعات الإسلامية في البورصة المصرية اليوم.
                    3. **أسهم تحت المراقبة / تحذيرات:** الأسهم التي تعاني من ضغط بيعي أو ضعف سيولة.
                    4. **توصية تنفيذية سريعة للمستثمر.**

                    ملاحظة صارمة: لا تذكر أي سهم تقليدي أو غير معتمد شرعياً في التقرير إطلاقاً.
                    """
                    
                    response = model.generate_content(prompt)
                    
                    # عرض التقرير داخل بطاقة منسقة
                    st.success("تم إعداد التقرير بنجاح!")
                    st.subheader("💡 التقرير التحليلي الموثوق")
                    st.markdown(response.text)
                    
                except Exception as e:
                    if "429" in str(e):
                        st.error("⏳ تم تجاوز حد الطلبات السريعة (Quota Exceeded). انتظر دقيقة واحدة واضغط على الزر مجدداً.")
                    else:
                        st.error(f"حدث خطأ أثناء طلب التحليل: {e}")
