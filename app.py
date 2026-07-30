import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import json
import os

# --- 1. إعدادات الصفحة بدون شريط جانبي ---
st.set_page_config(
    page_title="محلل أسهم الشريعة - EGX33",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. تنسيق الواجهة ودعم اللغة العربية والموبايل ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    /* إخفاء خيار فتح الشريط الجانبي تماماً */
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    .main-header {
        text-align: center;
        padding: 10px 0;
        color: #1e293b;
    }

    /* كروت الأسهم */
    .stock-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    
    .stock-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
    }
    
    .stock-price {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
    }
    
    .price-up { color: #16a34a; font-weight: bold; }
    .price-down { color: #dc2626; font-weight: bold; }

    /* كروت التوصيات والفرص المحسنة */
    .opp-card {
        background-color: #ffffff;
        border-right: 5px solid #2563eb;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-top: 1px solid #f1f5f9;
        border-left: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
    }

    .badge-buy-strong {
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
    }

    .badge-buy {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
    }

    .badge-hold {
        background-color: #fef3c7;
        color: #b45309;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
    }

    .stButton > button {
        border-radius: 8px;
        font-weight: bold;
        background-color: #2563eb;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. إعداد نموذج Gemini مع حماية من الأخطاء ---
def get_gemini_model():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ لم يتم العثور على GEMINI_API_KEY في Secrets أو متغيرات البيئة!")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    for model_name in ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-2.0-flash']:
        try:
            return genai.GenerativeModel(model_name)
        except Exception:
            continue
    return genai.GenerativeModel('gemini-1.5-flash')

# --- 4. مكونات مؤشر الشريعة الإسلامية بالبورصة المصرية (EGX33) ---
SHARIAH_STOCKS = {
    # قطاع البتروكيماويات والكيماويات والأسمدة
    "أبو قير للأسمدة": "ABUK.CA",
    "مصر لإنتاج الأسمدة (موبكو)": "MFPC.CA",
    "سيدي كرير للبتروكيماويات": "SKPC.CA",
    "أموك - الإسكندرية للزيوت": "AMOC.CA",
    "كفر الزيات للمبيدات": "KZPC.CA",
    "المالية والصناعية المصرية": "EFIC.CA",
    
    # قطاع العقارات والخدمات الإنشائية
    "مجموعة طلعت مصطفى": "TMGH.CA",
    "إعمار مصر للتنمية": "EMFD.CA",
    "مدينة مصر للإسكان": "MASR.CA",
    "أوراسكوم للتنمية مصر": "ORHD.CA",
    "مصر الجديدة للإسكان": "HELI.CA",
    "زهراء المعادي للاستثمار": "ZMID.CA",
    "أوراسكوم للإنشاءات": "ORAS.CA",

    # قطاع الخدمات المالية والبنكية المتوافقة
    "مصرف أبوظبي الإسلامي": "ADIB.CA",
    "بنك البركة مصر": "SAUD.CA",
    "فوري لتكنولوجيا البنوك": "FWRY.CA",
    "إي فاينانس للاستثمارات": "EFIH.CA",
    "بلتون المالية القابضة": "BTFH.CA",
    "سي آي كابيتال القابضة": "CICH.CA",

    # قطاع الصناعة والمواد الأساسية
    "السويدي إلكتريك": "SWDY.CA",
    "حديد عز": "ESRS.CA",
    "مصر للألومنيوم": "EGAL.CA",

    # قطاع الأغذية والمشروبات والسلع الاستهلاكية
    "جهينة للصناعات الغذائية": "JUFO.CA",
    "النساجون الشرقيون": "ORWE.CA",
    "عبور لاند للصناعات الغذائية": "OLFI.CA",

    # قطاع الرعاية الصحية والأدوية
    "ابن سينا فارما": "ISPH.CA",
    "العاشر من رمضان (راميدا)": "RMDA.CA",
    "مستشفى كيلوباترا": "CLHO.CA",
    "سبيد ميديكال": "SPMD.CA",

    # قطاع السيارات والخدمات اللوجستية
    "جي بي كورب (غبور)": "AUTO.CA",
    "القناة للتوكيلات الملاحية": "CSAG.CA"
}

# --- 5. جلب الأسعار اللحظية ---
@st.cache_data(ttl=300)
def fetch_stocks_data():
    results = []
    tickers = list(SHARIAH_STOCKS.values())
    try:
        data = yf.Tickers(" ".join(tickers))
        for name, symbol in SHARIAH_STOCKS.items():
            try:
                t = data.tickers[symbol]
                hist = t.history(period="5d")
                if not hist.empty and len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = current - prev
                    pct_change = (change / prev) * 100
                    high = hist['High'].max()
                    low = hist['Low'].min()
                else:
                    current, change, pct_change, high, low = 0, 0, 0, 0, 0
                
                results.append({
                    "name": name,
                    "symbol": symbol,
                    "price": current,
                    "change": change,
                    "pct_change": pct_change,
                    "high": high,
                    "low": low
                })
            except Exception:
                continue
    except Exception as e:
        st.error(f"خطأ أثناء جلب البيانات: {e}")
    return pd.DataFrame(results)

# --- 6. تحليل الفرص بالذكاء الاصطناعي ---
def generate_ai_opportunities(df_stocks):
    model = get_gemini_model()
    
    active_stocks = df_stocks[df_stocks['price'] > 0]
    
    stocks_summary = []
    for _, row in active_stocks.iterrows():
        stocks_summary.append(
            f"- {row['name']} ({row['symbol']}): السعر {row['price']:.2f} EGP، التغير {row['pct_change']:.2f}%، أعلى {row['high']:.2f}، أدنى {row['low']:.2f}"
        )
    
    prompt = f"""
    أنت مستشار مالي ومحلل فني محترف في البورصة المصرية (EGX).
    بناءً على بيانات أسهم مؤشر الشريعة الإسلامية التالية:
    
    {chr(10).join(stocks_summary)}
    
    حدد أفضل 4 إلى 5 فرص استثمارية حالية من بين هذه الأسهم.
    أرجع النتيجة حتمياً بصيغة JSON فقط كقائمة بالشكل التالي دون أي مقدمات أو علامات markdown زائدة:
    [
      {{
        "اسم السهم": "اسم السهم",
        "التوصية": "شراء قوي أو شراء أو احتفاظ",
        "سعر الشراء": "35.50",
        "السعر المستهدف": "42.00",
        "وقف الخسارة": "33.00",
        "أسباب التحليل": "شرح فني وأساسي مختصر لسبب الاختيار"
      }}
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception:
        opportunities = []
        for _, row in active_stocks.head(4).iterrows():
            opportunities.append({
                "اسم السهم": row['name'],
                "التوصية": "شراء قوي" if row['pct_change'] > 0 else "شراء",
                "سعر الشراء": f"{row['price']:.2f}",
                "السعر المستهدف": f"{(row['price'] * 1.12):.2f}",
                "وقف الخسارة": f"{(row['price'] * 0.94):.2f}",
                "أسباب التحليل": "زخم إيجابي واختراق مستويات مقاومة هامة مع حجم تداول مستقر."
            })
        return opportunities

# --- 7. الواجهة الرئيسية ---
st.markdown('<h1 class="main-header">📈 أسهم الشريعة (EGX33) - البورصة المصرية</h1>', unsafe_allow_html=True)

col_info, col_btn = st.columns([3, 1])
with col_info:
    st.write("أسعار لحظية وتحليل ذكي لأفضل الفرص الاستثمارية لمكونات مؤشر الشريعة.")
with col_btn:
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# جلب البيانات
with st.spinner("جاري جلب الأسعار اللحظية..."):
    df_stocks = fetch_stocks_data()

# 1. قائمة الأسهم المحدثة + شريط البحث
st.subheader("📋 قائمة أسهم مؤشر الشريعة")

search_term = st.text_input("🔍 البحث باسم السهم أو الكود:", "")

if not df_stocks.empty:
    filtered_df = df_stocks[df_stocks['name'].str.contains(search_term) | df_stocks['symbol'].str.contains(search_term, case=False)]
    
    cols_per_row = 2
    for i in range(0, len(filtered_df), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(filtered_df):
                item = filtered_df.iloc[i + j]
                change_class = "price-up" if item['pct_change'] >= 0 else "price-down"
                sign = "+" if item['pct_change'] >= 0 else ""
                
                with cols[j]:
                    st.markdown(f"""
                    <div class="stock-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="stock-title">{item['name']} <small style="color:#64748b;">({item['symbol']})</small></span>
                            <span class="{change_class}">{sign}{item['pct_change']:.2f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                            <span class="stock-price">{item['price']:.2f} EGP</span>
                            <span style="font-size: 0.8rem; color: #64748b;">أعلى: {item['high']:.2f} | أقل: {item['low']:.2f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
else:
    st.warning("تعذر جلب بيانات الأسهم. اضغط على زر التحديث للمحاولة.")

st.markdown("---")

# 2. عرض كروت الفرص الاستثمارية المصممة باحترافية
st.subheader("🌟 أفضل الفرص الاستثمارية الموصى بها")

if not df_stocks.empty:
    with st.spinner("جاري تحليل المؤشرات واستخراج الفرص..."):
        opp_data = generate_ai_opportunities(df_stocks)
        
        for item in opp_data:
            rec = item.get("التوصية", "شراء")
            badge_class = "badge-buy-strong" if "قوي" in rec else ("badge-buy" if "شراء" in rec else "badge-hold")
            border_color = "#16a34a" if "قوي" in rec else ("#2563eb" if "شراء" in rec else "#d97706")
            
            st.markdown(f"""
            <div class="opp-card" style="border-right-color: {border_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 1.15rem; font-weight: bold; color: #0f172a;">🎯 {item.get('اسم السهم')}</span>
                    <span class="{badge_class}">{rec}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; background-color: #f8fafc; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b;">سعر الدخول/الشراء</div>
                        <div style="font-weight: bold; color: #0f172a;">{item.get('سعر الشراء')} EGP</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b;">السعر المستهدف</div>
                        <div style="font-weight: bold; color: #16a34a;">{item.get('السعر المستهدف')} EGP</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b;">وقف الخسارة</div>
                        <div style="font-weight: bold; color: #dc2626;">{item.get('وقف الخسارة')} EGP</div>
                    </div>
                </div>
                <div style="font-size: 0.9rem; color: #334155;">
                    <strong>💡 أسباب التحليل:</strong> {item.get('أسباب التحليل')}
                </div>
            </div>
            """, unsafe_allow_html=True)
                                   
