import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from google import genai

# ---------------------------------------------------------
# 1. إعدادات الصفحة
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
# 3. قائمة الأسهم الإسلامية
# ---------------------------------------------------------
ISLAMIC_STOCKS = [
    {"name": "مصرف أبوظبي الإسلامي", "symbol": "ADIB"},
    {"name": "بنك البركة مصر", "symbol": "SAUD"},
    {"name": "بنك فيصل الإسلامي", "symbol": "FAIT"},
    {"name": "أموك للزيوت", "symbol": "AMOC"},
    {"name": "أبوقير للأسمدة", "symbol": "ABUK"},
    {"name": "موبكو للأسمدة", "symbol": "MFPC"},
    {"name": "سيدي كرير للبتروكيماويات", "symbol": "SKPC"},
    {"name": "مجموعة طلعت مصطفى", "symbol": "TMGH"},
    {"name": "مصر الجديدة للإسكان", "symbol": "HELI"},
    {"name": "مدينة مصر للإسكان", "symbol": "MASR"},
    {"name": "بالم هيلز للتعمير", "symbol": "PHDC"},
    {"name": "السويدي إليكتريك", "symbol": "SWDY"},
    {"name": "حديد عز", "symbol": "ESRS"},
    {"name": "المصرية للاتصالات", "symbol": "ETEL"},
    {"name": "فوري للمدفوعات", "symbol": "FWRY"},
    {"name": "ابن سينا فارما", "symbol": "ISPH"},
    {"name": "رميدا للأدوية", "symbol": "RMDA"},
    {"name": "سبيد ميديكال", "symbol": "SPMD"}
]

# ---------------------------------------------------------
# 4. محرك جلب الأسعار المباشر (بدون yfinance)
# ---------------------------------------------------------
def fetch_stock_direct(stock):
    symbol = stock["symbol"]
    url = f"https://www.mubasher.info/markets/EGX/stocks/{symbol}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # محاولة قراءة السعر والتغير
            price_elem = soup.find('span', {'class': 'market-summary__last-price'})
            change_elem = soup.find('span', {'class': 'market-summary__change'})
            
            price = float(price_elem.text.strip()) if price_elem else 0.0
            change = float(change_elem.text.strip().replace('%', '')) if change_elem else 0.0
            
            return {
                "الشركة": stock["name"],
                "الرمز": symbol,
                "السعر (ج.م)": price,
                "التغير %": change
            }
    except Exception:
        pass
    
    return {
        "الشركة": stock["name"],
        "الرمز": symbol,
        "السعر (ج.م)": "مباشر",
        "التغير %": 0.0
    }

def get_all_prices():
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_stock_direct, s) for s in ISLAMIC_STOCKS]
        for f in futures:
            res = f.result()
            if res:
                results.append(res)
    return pd.DataFrame(results)

# ---------------------------------------------------------
# 5. عرض البيانات
# ---------------------------------------------------------
if st.button("🔄 تحديث الأسعار الآن"):
    st.session_state['df_data'] = get_all_prices()

if 'df_data' not in st.session_state:
    st.session_state['df_data'] = get_all_prices()

df = st.session_state['df_data']
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")

# ---------------------------------------------------------
# 6. الذكاء الاصطناعي
# ---------------------------------------------------------
if st.button("✨ استخراج التقرير والتحليل الذكي"):
    if not api_key:
        st.warning("⚠️ يرجى أدخال مفتاح GEMINI_API_KEY أولاً.")
    else:
        with st.spinner("🧠 جاري إعداد التقرير بواسطة الذكاء الاصطناعي..."):
            try:
                client = genai.Client(api_key=api_key)
                
                # اختيار الموديل المتاح تلقائياً من الحساب
                models_list = list(client.models.list())
                chosen_model = None
                for m in models_list:
                    name = getattr(m, 'name', str(m))
                    if 'flash' in name.lower():
                        chosen_model = name
                        break
                if not chosen_model and models_list:
                    chosen_model = getattr(models_list[0], 'name', str(models_list[0]))

                table_text = df.to_string(index=False)
                
                prompt = f"""
                أنت محلل مالي خبير للأسهم الإسلامية بالبورصة المصرية.
                بيانات الأسهم الحالية:
                {table_text}

                المطلوب:
                1. جدول بأهم الفرص الشرائية (الشركة، الرمز، سعر الدخول، المستهدف، وقف الخسارة).
                2. ملخص للسيولة ونصحية استثمارية سريعة.
                """

                response = client.models.generate_content(
                    model=chosen_model,
                    contents=prompt
                )

                st.session_state['report_text'] = response.text
                st.rerun()

            except Exception as err:
                st.error(f"حدث خطأ أثناء طلب التقرير: {err}")

if 'report_text' in st.session_state:
    st.success("تم التقرير بنجاح! 🎯")
    st.markdown(st.session_state['report_text'])
    
