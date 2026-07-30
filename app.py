import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# ---------------------------------------------------------
# 1. إعدادات الصفحة والتصميم
# ---------------------------------------------------------
st.set_page_config(
    page_title="محلل الأسهم الإسلامية الشامل | EGX Shariah",
    page_icon="🕌",
    layout="wide"
)

st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.2em;
        font-weight: bold;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    div[data-testid="stMetricValue"] { font-size: 22px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🕌 منصة تحليل الأسهم الإسلامية (EGX Shariah)")
st.caption("تتبع شامل لجميع الأسهم المصرية المعتمدة شرعياً - تحديث يدوي حسب الطلب")

# ---------------------------------------------------------
# 2. جلب مفتاح Gemini API
# ---------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("🔑 أدخل مفتاح Gemini API:", type="password")

# ---------------------------------------------------------
# 3. القائمة الشاملة لجميع الأسهم الإسلامية بالبورصة المصرية
# ---------------------------------------------------------
ISLAMIC_STOCKS_MAP = {
    # البنوك والخدمات المالية
    "ADIB.CA": "مصرف أبوظبي الإسلامي",
    "SAUD.CA": "بنك البركة مصر",
    "FAIT.CA": "بنك فيصل الإسلامي (جنيه)",
    "CIEB.CA": "كريدي أجريكول مصر",
    
    # البتروكيماويات والأسمدة والطاقة
    "AMOC.CA": "الإسكندرية للزيوت (أموك)",
    "ABUK.CA": "أبوقير للأسمدة",
    "MFPC.CA": "مصر لإنتاج الأسمدة (موبكو)",
    "SKPC.CA": "سيدي كرير للبتروكيماويات",
    "KPRE.CA": "كفر الزيات للمبيدات",
    "EGAS.CA": "غاز مصر",
    
    # العقارات والتطوير العمراني
    "TMGH.CA": "مجموعة طلعت مصطفى",
    "HELI.CA": "مصر الجديدة للإسكان",
    "MASR.CA": "مدينة مصر للإسكان",
    "PHDC.CA": "بالم هيلز للتعمير",
    "OCDI.CA": "سوديك (6 أكتوبر)",
    "EMFD.CA": "إعمار مصر للتنمية",
    "ORHD.CA": "أوراسكوم للتنمية مصر",
    "UNIT.CA": "المتحدة للإسكان",
    
    # الصناعة والأغذية والدواجن
    "SWDY.CA": "السويدي إليكتريك",
    "ESRS.CA": "حديد عز",
    "JUFO.CA": "جهينة للصناعات الغذائية",
    "OLFI.CA": "عبور لاند للصناعات الغذائية",
    "EFID.CA": "إيديتا للصناعات الغذائية",
    "DOMH.CA": "دومتي",
    "ORWE.CA": "النساجون الشرقيون",
    "ALCN.CA": "الإسكندرية لتداول البضائع",
    "EGAL.CA": "مصر للألومنيوم",
    "MCQE.CA": "مصر بني سويف للأسمنت",
    "ARCC.CA": "العربية للأسمنت",
    "ATQA.CA": "مصر الوطنية للصلب (عتاقة)",
    
    # التكنولوجيا والاتصالات والخدمات الرقمية
    "ETEL.CA": "المصرية للاتصالات",
    "FWRY.CA": "فوري للمدفوعات",
    "EFIH.CA": "إي فاينانس للإستثمارات",
    "RAYA.CA": "راية القابضة",
    
    # الرعاية الصحية والأدوية
    "ISPH.CA": "ابن سينا فارما",
    "RMDA.CA": "رميدا للأدوية",
    "CLHO.CA": "مستشفى كليوباترا",
    "SPMD.CA": "سبيد ميديكال"
}

# ---------------------------------------------------------
# 4. محرك جلب الأسعار
# ---------------------------------------------------------
def fetch_single_stock(ticker, name):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if not hist.empty and len(hist) >= 1:
            last_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else last_price
            
            change_percent = 0.0
            if prev_price > 0:
                change_percent = ((last_price - prev_price) / prev_price) * 100
                
            volume = hist['Volume'].iloc[-1]
            
            return {
                "الشركة": name,
                "الرمز": ticker.replace(".CA", ""),
                "السعر الحالي (ج.م)": round(last_price, 2),
                "التغير %": round(change_percent, 2),
                "حجم التداول": int(volume)
            }
    except Exception:
        pass
    return None

def fetch_all_islamic_prices(stocks_dict):
    data_list = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [
            executor.submit(fetch_single_stock, ticker, name)
            for ticker, name in stocks_dict.items()
        ]
        for future in futures:
            res = future.result()
            if res:
                data_list.append(res)
                
    df = pd.DataFrame(data_list)
    if not df.empty:
        df = df.sort_values(by="حجم التداول", ascending=False)
    return df

# ---------------------------------------------------------
# 5. التحكم اليدوي لتحديث الأسعار
# ---------------------------------------------------------
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("🔄 تحديث أسعار الأسهم الآن"):
        with st.spinner("⏳ جاري سحب أحدث الأسعار..."):
            st.session_state['prices_df'] = fetch_all_islamic_prices(ISLAMIC_STOCKS_MAP)

if 'prices_df' not in st.session_state:
    st.session_state['prices_df'] = fetch_all_islamic_prices(ISLAMIC_STOCKS_MAP)

df_prices = st.session_state['prices_df']

# ---------------------------------------------------------
# 6. عرض جدول الأسعار والبيانات
# ---------------------------------------------------------
if df_prices.empty:
    st.error("⚠️ تعذر جلب البيانات. اضغط على زر التحديث أعلاه لإعادة المحاولة.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="إجمالي الأسهم المتابعة", value=f"{len(df_prices)} سهم إسلامي")
    with col2:
        st.metric(label="وضع التحديث", value="يدوي 100%", delta="محتفظ بالكوتا")
    with col3:
        top_gainer = df_prices.loc[df_prices['التغير %'].idxmax()] if not df_prices.empty else None
        if top_gainer is not None:
            st.metric(label="الأعلى صعوداً", value=f"{top_gainer['الشركة']}", delta=f"{top_gainer['التغير %']}%")

    st.markdown("---")
    st.subheader("📊 جدول أسعار الأسهم الإسلامية")
    
    st.dataframe(
        df_prices, 
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    st.markdown("---")
    
    # ---------------------------------------------------------
    # 7. زر التحليل الذكي (تم تعديل اسم الموديل إلى gemini-1.5-flash)
    # ---------------------------------------------------------
    if st.button("✨ استخراج التقرير والتحليل الذكي للأسهم"):
        if not api_key:
            st.warning("⚠️ برجاء إدخال مفتاح Gemini API في الشريط الجانبي أو في Secrets.")
        else:
            with st.spinner("🧠 جاري تحليل البيانات وصياغة التوصيات..."):
                try:
                    genai.configure(api_key=api_key)
                    # تعديل اسم الموديل ليكون شغال ومستقر 100%
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"""
                    أنت خبير ومحلل مالي متخصص حصرياً في الأسهم المتوافقة مع الشريعة الإسلامية بالبورصة المصرية (EGX Shariah).
                    إليك جدول البيانات اللحظية لجميع الأسهم الإسلامية المتداولة حالياً:
                    
                    {df_prices.to_string(index=False)}
                    
                    يرجى إعداد تقرير مالي دقيق ومحترف وفق الأقسام التالية:

                    1. **🎯 أفضل الفرص الشرائية اللحظية (جدول منظم):**
                       اختر أفضل 5 إلى 7 أسهم إيجابية وضعها في جدول يحتوي على:
                       - اسم الشركة
                       - الرمز (Ticker)
                       - السعر الحالي
                       - نقطة الدخول المقترحة
                       - المستهدف الأول
                       - نسبة الربح المتوقعة (%)
                       - وقف الخسارة (Stop Loss)

                    2. **🌊 تحليل اتجاهات السيولة والقطاعات:** تحليل سريع للقطاعات الأكثر إقبالاً.
                    3. **⚠️ أسهم تحت المراقبة / تحذيرات:** الأسهم التي بها ضغط بيعي أو ضعف سيولة.
                    4. **💡 نصيحة استثمارية سريعة.**

                    تنبيه: لا تدرج أي شركة خارج هذه القائمة المعتمدة شرعياً.
                    """
                    
                    response = model.generate_content(prompt)
                    st.session_state['latest_report'] = response.text
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"حدث خطأ أثناء تحليل البيانات: {e}")

    # عرض التقرير
    if 'latest_report' in st.session_state:
        st.success("تم إعداد التقرير بنجاح!")
        st.subheader("💡 التقرير التحليلي الشامل")
        st.markdown(st.session_state['latest_report'])
                  
