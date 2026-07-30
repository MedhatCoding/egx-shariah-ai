import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# ---------------------------------------------------------
# 1. إعدادات الصفحة
# ---------------------------------------------------------
st.set_page_config(
    page_title="محلل الأسهم الإسلامية الشامل | EGX Shariah",
    page_icon="🕌",
    layout="wide"
)

st.title("🕌 منصة تحليل الأسهم الإسلامية (EGX Shariah)")
st.caption("تتبع شامل لجميع الأسهم المصرية المعتمدة شرعياً - تحديث يدوي حسب الطلب")

# ---------------------------------------------------------
# 2. جلب مفتاح API
# ---------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("🔑 أدخل مفتاح Gemini API:", type="password")

# ---------------------------------------------------------
# 3. قائمة الأسهم الإسلامية
# ---------------------------------------------------------
ISLAMIC_STOCKS_MAP = {
    "ADIB.CA": "مصرف أبوظبي الإسلامي",
    "SAUD.CA": "بنك البركة مصر",
    "FAIT.CA": "بنك فيصل الإسلامي (جنيه)",
    "CIEB.CA": "كريدي أجريكول مصر",
    "AMOC.CA": "الإسكندرية للزيوت (أموك)",
    "ABUK.CA": "أبوقير للأسمدة",
    "MFPC.CA": "مصر لإنتاج الأسمدة (موبكو)",
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
# 4. محرك الأسعار
# ---------------------------------------------------------
def fetch_single_stock(ticker, name):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if not hist.empty and len(hist) >= 1:
            last_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else last_price
            change_percent = ((last_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0.0
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
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_single_stock, ticker, name) for ticker, name in stocks_dict.items()]
        for future in futures:
            res = future.result()
            if res:
                data_list.append(res)
    df = pd.DataFrame(data_list)
    if not df.empty:
        df = df.sort_values(by="حجم التداول", ascending=False)
    return df

# ---------------------------------------------------------
# 5. عرض البيانات
# ---------------------------------------------------------
if st.button("🔄 تحديث أسعار الأسهم الآن"):
    st.session_state['prices_df'] = fetch_all_islamic_prices(ISLAMIC_STOCKS_MAP)

if 'prices_df' not in st.session_state:
    st.session_state['prices_df'] = fetch_all_islamic_prices(ISLAMIC_STOCKS_MAP)

df_prices = st.session_state['prices_df']

if df_prices.empty:
    st.error("⚠️ تعذر جلب البيانات. اضغط على زر التحديث أعلاه.")
else:
    st.dataframe(df_prices, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ---------------------------------------------------------
    # 6. زر التحليل الذكي
    # ---------------------------------------------------------
    if st.button("✨ استخراج التقرير والتحليل الذكي للأسهم"):
        if not api_key:
            st.warning("⚠️ برجاء إدخال مفتاح Gemini API.")
        else:
            with st.spinner("🧠 جاري التحليل..."):
                try:
                    genai.configure(api_key=api_key)
                    # موديل ثابت ومباشر ورسمي بدون مسارات معقدة
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    # نرسل أعلى 10 أسهم فقط لمنع أي بطء أو تجاوز كوتا
                    top_data = df_prices.head(10).to_string(index=False)
                    
                    prompt = f"""
                    أنت خبير مالي للأسهم الإسلامية بالبورصة المصرية.
                    إليك بيانات أنشط الأسهم اليوم:
                    {top_data}
                    
                    قدم تقرير سريع ومختصر يحتوي على:
                    1. أفضل الفرص الشرائية (الشركة، سعر الدخول، المستهدف، وقف الخسارة).
                    2. ملخص حالة السوق.
                    """
                    
                    response = model.generate_content(prompt)
                    st.session_state['latest_report'] = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"حدث خطأ أثناء تحليل البيانات: {e}")

    if 'latest_report' in st.session_state:
        st.success("تم إعداد التقرير بنجاح!")
        st.markdown(st.session_state['latest_report'])
        
