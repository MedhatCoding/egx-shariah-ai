import streamlit as st
import google.generativeai as genai
import yfinance as ticker_data
import pandas as pd
import os

# --- 1. إعدادات الصفحة والواجهة الاحترافية ---
st.set_page_config(
    page_title="محلل EGX الشريعة",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تحسين مظهر الواجهة بدعم اتجاه النص العربي (RTL)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .stButton>button {
        width: 100%;
        background-color: #0d6efd;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. جلب API Key تلقائياً دون مطالبات تكرارية ---
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif os.getenv("GEMINI_API_KEY"):
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ لم يتم العثور على API Key! يرجى إضافته في Streamlit Secrets أو متغيرات البيئة.")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. قائمة أهم أسهم الشريعة الإسلامية بالبورصة المصرية (EGX) ---
SHARIAH_STOCKS = {
    "أبو قير للأساد": "ABUK.CA",
    "مصر لإنتاج الأسمدة (موبكو)": "MFPC.CA",
    "السويدي إلكتريك": "SWDY.CA",
    "طلعت مصطفى": "TMGH.CA",
    "فوري لتكنولوجيا البنوك": "FWRY.CA",
    "مصرف أبوظبي الإسلامي": "ADIB.CA",
    "سي دي كرير": "SKPC.CA",
    "إي فاينانس": "EFIH.CA",
    "النساجون الشرقيون": "ORWE.CA",
    "جهينة للصناعات الغذائية": "JUFO.CA"
}

# --- 4. الشريط الجانبي ---
st.sidebar.title("📌 الخيارات")
selected_stock_name = st.sidebar.selectbox("اختر السهم متوافق مع الشريعة:", list(SHARIAH_STOCKS.keys()))
selected_ticker = SHARIAH_STOCKS[selected_stock_name]

refresh_btn = st.sidebar.button("🔄 تحديث البيانات والتحليل")

# --- 5. دالة جلب البيانات والأخبار ---
def get_stock_data(symbol):
    stock = ticker_data.Ticker(symbol)
    df = stock.history(period="1mo")
    info = stock.info
    news = stock.news[:3] if stock.news else []
    return df, info, news

# --- 6. الصفحة الرئيسية ---
st.title("📈 المحلل الذكي - أسهم الشريعة بالبورصة المصرية")
st.write(f"عرض تحليلي احترافي للسهم: **{selected_stock_name}** (`{selected_ticker}`)")

df, info, news = get_stock_data(selected_ticker)

if not df.empty:
    last_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2]
    change = last_price - prev_price
    pct_change = (change / prev_price) * 100

    # عرض كروت إحصائية شريعة وسريعة
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("السعر الحالي", f"{last_price:.2f} EGP", f"{change:+.2f} ({pct_change:+.2f}%)")
    col2.metric("أعلى سعر (أشهر)", f"{df['High'].max():.2f} EGP")
    col3.metric("أقل سعر (أشهر)", f"{df['Low'].min():.2f} EGP")
    col4.metric("حجم التداول الأخير", f"{int(df['Volume'].iloc[-1]):,}")

    st.markdown("---")

    # زر التحليل أو التحديث
    if refresh_btn or "analysis" not in st.session_state:
        with st.spinner("جاري تحليل المؤشرات والأخبار عبر الذكاء الاصطناعي..."):
            
            # تجهيز ملخص الأخبار
            news_text = ""
            for n in news:
                news_text += f"- {n.get('title', '')}\n"

            # صياغة الموجه للذكاء الاصطناعي كمستثمر محترف
            prompt = f"""
            أنت مستشار مالي ومحلل فني وأساسي محترف خبير في البورصة المصرية (EGX).
            قم بتحليل سهم ({selected_stock_name}) المتوافق مع الشريعة الإسلامية بناءً على البيانات التالية:

            - السعر اللحظي الأخير: {last_price:.2f} EGP
            - نسبة التغير الأخيرة: {pct_change:.2f}%
            - أعلى/أقل سعر خلال شهر: {df['High'].max():.2f} / {df['Low'].min():.2f} EGP
            - متوسط التداول: {df['Volume'].mean():.0f}
            - أهم الأخبار الحديثة للسهم:
            {news_text if news_text else "لا توجد أخبار جوهرية مسجلة حديثاً."}

            يرجى تقديم تقرير مالي محترف واحترافي يغطي الأجزاء التالية بشكل مباشر وبسيط:
            1. **التقييم العام والفرصة**: (هل توجد فرصة شراء/احتفاظ/بيع؟)
            2. **سعر الشراء الافتراضي (الدخول المناسب)**
            3. **السعر المستهدف (Target Price)**
            4. **وقف الخسارة (Stop Loss)**
            5. **أسباب التحليل الفنية والأساسية**: (بناءً على اتجاه السعر والمؤشرات)
            6. **نصيحة الاستثمار للمستثمر**: (قصيرة الأجل أم طويلة الأجل؟)
            """

            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            st.session_state.analysis = response.text

    # عرض التقرير
    st.subheader("💡 تقرير التحليل المالي والفرص")
    st.markdown(st.session_state.analysis)

else:
    st.warning("تعذر جلب بيانات السهم حالياً. اضغط على زر التحديث للمحاولة مرة أخرى.")
