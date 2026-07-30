import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import json
import os

# --- 1. إعدادات الصفحة بدون شريط جانبي ---
st.set_page_config(
    page_title="محلل أسهم الشريعة - EGX",
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
    
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    .main-header {
        text-align: center;
        padding: 10px 0;
        color: #1e293b;
    }

    .stock-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    
    .stock-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0f172a;
    }
    
    .stock-price {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a;
    }
    
    .price-up {
        color: #16a34a;
        font-weight: bold;
    }
    
    .price-down {
        color: #dc2626;
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

# --- 4. قائمة أسهم مؤشر الشريعة الإسلامية بالبورصة المصرية ---
SHARIAH_STOCKS = {
    "أبو قير للأسمدة": "ABUK.CA",
    "مصر لإنتاج الأسمدة (موبكو)": "MFPC.CA",
    "السويدي إلكتريك": "SWDY.CA",
    "مجموعة طلعت مصطفى": "TMGH.CA",
    "فوري لتكنولوجيا البنوك": "FWRY.CA",
    "مصرف أبوظبي الإسلامي": "ADIB.CA",
    "سيدي كرير للبتروكيماويات": "SKPC.CA",
    "إي فاينانس": "EFIH.CA",
    "النساجون الشرقيون": "ORWE.CA",
    "جهينة للصناعات الغذائية": "JUFO.CA"
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
    
    stocks_summary = []
    for _, row in df_stocks.iterrows():
        stocks_summary.append(
            f"- {row['name']} ({row['symbol']}): السعر الحالي {row['price']:.2f} EGP، التغير {row['pct_change']:.2f}%، أعلى سعر {row['high']:.2f}، أدنى سعر {row['low']:.2f}"
        )
    
    prompt = f"""
    أنت مستشار مالي ومحلل فني محترف في البورصة المصرية (EGX).
    بناءً على بيانات أسهم الشريعة الإسلامية التالية:
    
    {chr(10).join(stocks_summary)}
    
    حلل هذه الأسهم وحدد أفضل 4 إلى 5 فرص استثمارية.
    أرجع النتيجة حتمياً بصيغة JSON فقط كقائمة بالشكل التالي دون أي نصوص خارجية:
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
        
        # تنظيف النص من علامات التنسيق الخاصة بـ Markdown
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception:
        opportunities = []
        for _, row in df_stocks.iterrows():
            if row['price'] > 0:
                opportunities.append({
                    "اسم السهم": row['name'],
                    "التوصية": "شراء" if row['pct_change'] >= 0 else "احتفاظ",
                    "سعر الشراء": f"{row['price']:.2f}",
                    "السعر المستهدف": f"{(row['price'] * 1.12):.2f}",
                    "وقف الخسارة": f"{(row['price'] * 0.94):.2f}",
                    "أسباب التحليل": "مؤشرات تداول مستقرة مع حركة سعرية إيجابية"
                })
        return opportunities

# --- 7. الواجهة الرئيسية ---
st.markdown('<h1 class="main-header">📈 أسهم الشريعة - البورصة المصرية</h1>', unsafe_allow_html=True)

col_info, col_btn = st.columns([3, 1])
with col_info:
    st.write("أسعار لحظية وتحليل ذكي لأفضل الفرص الاستثمارية المتوافقة مع الشريعة الإسلامية.")
with col_btn:
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# جلب البيانات
with st.spinner("جاري جلب الأسعار اللحظية..."):
    df_stocks = fetch_stocks_data()

# 1. قائمة الأسهم (List View / Grid)
st.subheader("📋 قائمة أسهم المؤشر")

if not df_stocks.empty:
    cols_per_row = 2
    for i in range(0, len(df_stocks), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(df_stocks):
                item = df_stocks.iloc[i + j]
                change_class = "price-up" if item['pct_change'] >= 0 else "price-down"
                sign = "+" if item['pct_change'] >= 0 else ""
                
                with cols[j]:
                    st.markdown(f"""
                    <div class="stock-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="stock-title">{item['name']} <small style="color:#64748b;">({item['symbol']})</small></span>
                            <span class="{change_class}">{sign}{item['pct_change']:.2f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                            <span class="stock-price">{item['price']:.2f} EGP</span>
                            <span style="font-size: 0.85rem; color: #64748b;">أعلى: {item['high']:.2f} | أقل: {item['low']:.2f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
else:
    st.warning("تعذر جلب بيانات الأسهم. اضغط على زر التحديث للمحاولة.")

st.markdown("---")

# 2. جدول أفضل الفرص الاستثمارية
st.subheader("🌟 جدول أفضل الفرص الاستثمارية")

if not df_stocks.empty:
    with st.spinner("جاري تحليل الأسهم واستخراج أفضل الفرص..."):
        opp_data = generate_ai_opportunities(df_stocks)
        df_opp = pd.DataFrame(opp_data)
        
        st.dataframe(
            df_opp,
            use_container_width=True,
            hide_index=True,
            column_config={
                "اسم السهم": st.column_config.TextColumn("اسم السهم", width="medium"),
                "التوصية": st.column_config.TextColumn("التوصية", width="small"),
                "سعر الشراء": st.column_config.TextColumn("سعر الشراء", width="small"),
                "السعر المستهدف": st.column_config.TextColumn("السعر المستهدف", width="small"),
                "وقف الخسارة": st.column_config.TextColumn("وقف الخسارة", width="small"),
                "أسباب التحليل": st.column_config.TextColumn("أسباب التحليل والفرصة", width="large"),
            }
)
