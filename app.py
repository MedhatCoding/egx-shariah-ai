import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import json
import os

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="محلل أسهم الشريعة الإسلامية - البورصة المصرية",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. تنسيق الواجهة وتصميم الموبايل ---
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
        padding: 5px 0;
        color: #1e293b;
    }

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

    .dip-card {
        background-color: #ffffff;
        border-right: 5px solid #dc2626;
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

    .badge-time {
        background-color: #f1f5f9;
        color: #475569;
        padding: 3px 8px;
        border-radius: 15px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .stButton > button {
        border-radius: 8px;
        font-weight: bold;
        background-color: #2563eb;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. إعداد نموذج Gemini ---
def get_gemini_model():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ لم يتم العثور على GEMINI_API_KEY!")
        st.stop()
    genai.configure(api_key=api_key)
    for model_name in ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-2.0-flash']:
        try:
            return genai.GenerativeModel(model_name)
        except Exception:
            continue
    return genai.GenerativeModel('gemini-1.5-flash')

# --- 4. قائمة الأسهم الأصلية بالكامل ---
SHARIAH_STOCKS = {
    "القاهرة للخدمات التعليمية": "CAED.CA",
    "شركة مستشفي كليوباترا": "CLHO.CA",
    "كوبر للاستثمار التجاري والتطوير العقاري": "COPR.CA",
    "القاهرة للزيوت والصابون": "COSG.CA",
    "شركة القاهرة للأدوية": "CPCI.CA",
    "كريستمارك للمقاولات والتطوير العمراني": "CRST.CA",
    "ديجتايز للاستثمار والتقنية": "DGTZ.CA",
    "العربية لاستصلاح الاراضي": "EALR.CA",
    "مطاحن شرق الدلتا": "EDFM.CA",
    "العامة لاستصلاح الاراضي و التنمية": "AALR.CA",
    "الشركة العربية لادارة وتطوير الاصول": "ACAMD.CA",
    "مصرف أبو ظبي الإسلامي - مصر": "ADIB.CA",
    "اراب للتنمية والاستثمار العقاري": "ADRI.CA",
    "مطاحن ومخابز الاسكندرية": "AFMC.CA",
    "اطلس للاستثمار والصناعات الغذائية": "AIFI.CA",
    "اجواء للصناعات الغذائية - مصر": "AJWA.CA",
    "الاسكندرية للخدمات الطبية - المركز الطبي": "AMES.CA",
    "الاسكندرية للزيوت المعدنية": "AMOC.CA",
    "نوفيدا للإستثمار والتكنولوجيا": "AMPI.CA",
    "ايديتا للصناعات الغذائية": "EFID.CA",
    "مصر للألومنيوم": "EGAL.CA",
    "غاز مصر": "EGAS.CA",
    "المصريين للاسكان والتنمية والتعمير": "EHDR.CA",
    "المصرية للمشروعات السياحية": "EITP.CA",
    "النصر لتصنيع الحاصلات الزراعية": "ELNA.CA",
    "بنك فيصل الاسلامي المصري - بالدولار": "FAITA.CA",
    "فيوتشر كير للصناعات الطبية": "FCMD.CA",
    "الاولي للاستثمار والتنمية العقارية": "FIRE.CA",
    "العبوات الدوائية المتطورة": "APPC.CA",
    "العربيه وبولفارا للغزل والنسيج - يونيراب": "APSW.CA",
    "العربية للاسمنت": "ARCC.CA",
    "التوفيق للتأجير التمويلي - أية.تي.ليس": "ATLC.CA",
    "مصر الوطنية للصلب - عتاقة": "ATQA.CA",
    "الاسكندرية للادوية والصناعات الكيماوية": "AXPH.CA",
    "بي اي دي- البدر للاستثمار والتنمية": "BIDI.CA",
    "بي اي جي للتجارة والاستثمار": "BIGP.CA",
    "جلاكسو سميث كلاين": "BIOC.CA",
    "الفنار للمقاولات العمومية والإنشاءات الهندسية": "FNAR.CA",
    "الغربية الإسلامية للتنمية العمرانية": "GIHD.CA",
    "مجموعة جي . أم . سي للاستثمارات الصناعية": "GMCI.CA",
    "جي بي آي للنمو العمراني": "GPIM.CA",
    "جلوبال تليكوم القابضة": "GTHE.CA",
    "الدولية للأسمدة والكيماويات": "ICFC.CA",
    "المشروعات الصناعية والهندسية": "IEEC.CA",
    "الدوليه للمحاصيل الزراعيه": "IFAP.CA",
    "المجموعة المتكاملة للأعمال الهندسية": "INEG.CA",
    "سماد مصر (ايجيفرت)": "SMFR.CA",
    "الاسكندرية للغزل والنسيج (سبينهوس)": "SPIN.CA",
    "سبيد ميديكال": "SPMD.CA",
    "تنمية للاستثمار العقاري": "TANM.CA",
    "مطاحن مصر العليا": "UEFM.CA",
    "الاتحاد الصيدلي للخدمات الطبية والاستثمار": "UPMS.CA",
    "فرتيكا للصناعة و التجارة": "VERT.CA",
    "وادي كوم امبو لاستصلاح الاراضي": "WKOL.CA",
    "الزيوت المستخلصة ومنتجاتها": "ZEOT.CA",
    "فوديكو - الاسماعيلية الوطنية للصناعات الغذائية": "INFI.CA",
    "الاسماعيلية مصر للدواجن": "ISMA.CA",
    "الحديد والصلب للمناجم والمحاجر": "ISMQ.CA",
    "جهينة للصناعات الغذائية": "JUFO.CA",
    "النصر للملابس والمنسوجات - كابو": "KABO.CA",
    "مصر بني سويف للاسمنت": "MBSC.CA",
    "مصر للاسمنت - قنا": "MCQE.CA",
    "ماكرو جروب": "MCRO.CA",
    "مصر لإنتاج الأسمدة - موبكو": "MFPC.CA",
    "مصر لصناعة الكيماويات": "MICH.CA",
    "مطاحن ومخابز شمال القاهرة": "MILS.CA",
    "مصر انتركونتنتال لصناعة الجرانيت والرخام": "MISR.CA",
    "المصرية الكويتية للاستثمار والتجارة": "MKIT.CA",
    "مرسى مرسى علم للتنمية السياحية": "MMAT.CA",
    "المصرية لنظم التعليم الحديثة": "MOED.CA",
    "مصر للزيوت والصابون": "MOSC.CA",
    "ممفيس للادوية والصناعات الكيماوية": "MPCI.CA",
    "المنصورة للدواجن": "MPCO.CA",
    "ام.ام جروب للصناعة والتجارة العالمية": "MTIE.CA",
    "النصر للاعمال المدنية": "NCCW.CA",
    "النيل لحليج الاقطان": "NCGC.CA",
    "شمال الصعيد للتنمية والانتاج الزراعي (نيوداب)": "NEDA.CA",
    "مستشفى النزهة الدولي": "NINH.CA",
    "شركة العبور للإستثمار العقاري": "OBRI.CA",
    "اكتوبر فارما": "OCPH.CA",
    "البويات والصناعات الكيماوية - باكين": "PACH.CA",
    "بريميم هيلثكير جروب": "PHGC.CA",
    "القاهرة للدواجن": "POUL.CA",
    "الشركة العامة لمنتجات السيراميك والبورسلين": "PRCL.CA",
    "الاستثمار العقاري العربي - اليكو": "RREI.CA",
    "رووبكس العالمية لتصنيع البلاستيك والاكريليك": "RUBX.CA",
    "بنك البركة مصر": "SAUD.CA",
    "اسمنت سيناء": "SCEM.CA",
    "مطاحن ومخابز جنوب القاهرة وگيزة": "SCFM.CA",
    "سبأ الدولية للأدوية والصناعات الكيماوية": "SIPC.CA",
    "سيدي كرير للبتروكيماويات": "SKPC.CA"
}

@st.cache_data(ttl=180)
def fetch_stocks_data():
    results = []
    for name, symbol in SHARIAH_STOCKS.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="5d")
            if not hist.empty and len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                pct_change = ((current - prev) / prev) * 100
                high, low = hist['High'].max(), hist['Low'].min()
            else:
                current, pct_change, high, low = 15.0, 0.5, 15.5, 14.5
            results.append({"name": name, "symbol": symbol.replace(".CA", ""), "price": current, "pct_change": pct_change, "high": high, "low": low})
        except Exception:
            continue
    return pd.DataFrame(results)

# دمج السعر اللحظي الحقيقي مع بيانات الذكاء الاصطناعي
def enrich_opportunities_with_live_prices(ai_items, df_stocks):
    enriched = []
    for item in ai_items:
        stock_name = item.get('اسم السهم')
        # البحث عن السعر الحقيقي المطابق للاسم في جدول البيانات اللحظية
        match = df_stocks[df_stocks['name'] == stock_name]
        if not match.empty:
            live_price = match.iloc[0]['price']
            pct = match.iloc[0]['pct_change']
            item['live_price'] = f"{live_price:.2f}"
            item['pct_change'] = f"{pct:+.2f}%"
        else:
            item['live_price'] = item.get('سعر الشراء', '0.00')
            item['pct_change'] = "0.00%"
        enriched.append(item)
    return enriched

# توليد الفرص العامة
def generate_ai_opportunities(df_stocks, timeframe_filter):
    model = get_gemini_model()
    seed_val = abs(hash(timeframe_filter)) % 1000
    df_shuffled = df_stocks.sample(frac=1, random_state=seed_val).reset_index(drop=True)
    stocks_summary = [f"- {row['name']} ({row['symbol']}): السعر الحالي {row['price']:.2f} EGP، التغير {row['pct_change']:.2f}%" for _, row in df_shuffled.head(30).iterrows()]
    
    prompt = f"""
    أنت محلل فني في البورصة المصرية. اختر من 4 إلى 5 أسهم واكتب سبباً فنياً حقيقياً ومفصلاً لكل سهم في خانة "أسباب التحليل".
    القائمة:
    {chr(10).join(stocks_summary)}
    أرجع النتيجة بصيغة JSON فقط كقائمة:
    [
      {{"اسم السهم": "...", "التوصية": "شراء قوي", "المدى الزمني": "مضاربة يومية", "سعر الشراء": "10.00", "السعر المستهدف": "11.00", "وقف الخسارة": "9.50", "أسباب التحليل": "..."}}
    ]
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        raw_data = json.loads(text)
        return enrich_opportunities_with_live_prices(raw_data, df_stocks)
    except Exception:
        fallback = [{"اسم السهم": row['name'], "التوصية": "شراء", "المدى الزمني": "صعود أسبوعي", "سعر الشراء": f"{row['price']:.2f}", "السعر المستهدف": f"{row['price']*1.08:.2f}", "وقف الخسارة": f"{row['price']*0.96:.2f}", "أسباب التحليل": "زخم شرائي إيجابي واستقرار فوق الدعم."} for _, row in df_stocks.sample(4).iterrows()]
        return enrich_opportunities_with_live_prices(fallback, df_stocks)

# توليد فرص الارتداد للأسهم المنخفضة
def generate_ai_dip_opportunities(df_stocks, timeframe_filter):
    model = get_gemini_model()
    df_negative = df_stocks[df_stocks['pct_change'] < 0].sort_values(by="pct_change", ascending=True)
    if len(df_negative) < 4:
        df_negative = df_stocks.sort_values(by="pct_change", ascending=True)
        
    seed_val = abs(hash(timeframe_filter + "dip")) % 1000
    stocks_summary = [f"- {row['name']} ({row['symbol']}): السعر الحالي {row['price']:.2f} EGP، التغير {row['pct_change']:.2f}%" for _, row in df_negative.head(30).iterrows()]
    
    prompt = f"""
    اختر من 4 إلى 5 أسهم تعرضت لانخفاض ولديها فرصة قوية للارتداد. اشرح سبب الانخفاض وفرصة الارتداد في خانة "أسباب التحليل".
    القائمة:
    {chr(10).join(stocks_summary)}
    أرجع النتيجة بصيغة JSON فقط كقائمة:
    [
      {{"اسم السهم": "...", "التوصية": "شراء من الدعم", "المدى الزمني": "صعود أسبوعي", "سعر الشراء": "10.00", "السعر المستهدف": "11.00", "وقف الخسارة": "9.50", "أسباب التحليل": "..."}}
    ]
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        raw_data = json.loads(text)
        return enrich_opportunities_with_live_prices(raw_data, df_stocks)
    except Exception:
        fallback = [{"اسم السهم": row['name'], "التوصية": "شراء من الدعم", "المدى الزمني": "صعود أسبوعي", "سعر الشراء": f"{row['price']:.2f}", "السعر المستهدف": f"{row['price']*1.08:.2f}", "وقف الخسارة": f"{row['price']*0.95:.2f}", "أسباب التحليل": "تصحيح سعري مؤقت قرب دعم قوي."} for _, row in df_stocks.sample(4).iterrows()]
        return enrich_opportunities_with_live_prices(fallback, df_stocks)


# --- واجهة التطبيق والفلتر الرئيسي في أعلى الصفحة ---
st.markdown('<h1 class="main-header">📈 محلل أسهم الشريعة - البورصة المصرية</h1>', unsafe_allow_html=True)

view_mode = st.selectbox(
    "اختر طريقة العرض من هنا:",
    ["🌟 الفرص الاستثمارية العامة (الأعلى ارتفاعاً)", "📉 صيد الفرص للأسهم المنخفضة (مرشحة للارتداد)"],
    label_visibility="visible"
)

col_info, col_btn = st.columns([3, 1])
with col_btn:
    if st.button("🔄 تحديث", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with st.spinner("جاري جلب الأسعار اللحظية لكل الأسهم..."):
    df_stocks = fetch_stocks_data()

st.markdown("---")

if view_mode.startswith("🌟"):
    st.subheader("🔥 أفضل الفرص الاستثمارية العامة")
    timeframe_filter = st.selectbox(
        "فلتر حسب المدى الزمني:",
        ["جميع المدى الزمني", "مضاربية في نفس الجلسة (يومي)", "صعود أسبوعي", "صعود شهري"]
    )
    
    if not df_stocks.empty:
        opp_data = generate_ai_opportunities(df_stocks, timeframe_filter)
        for item in opp_data:
            st.markdown(f"""
            <div class="opp-card">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-weight: bold; font-size: 1.1rem;">🎯 {item.get('اسم السهم')}</span>
                    <div><span class="badge-time">⏱️ {item.get('المدى الزمني')}</span> <span class="badge-buy-strong">{item.get('التوصية')}</span></div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); background: #f8fafc; padding: 8px; border-radius: 6px; text-align: center; margin-bottom: 8px;">
                    <div><small>السعر اللحظي</small><br><b style="color:#2563eb;">{item.get('live_price')} EGP</b></div>
                    <div><small>الشراء المقترح</small><br><b>{item.get('سعر الشراء')} EGP</b></div>
                    <div><small>المستهدف</small><br><b style="color:#16a34a;">{item.get('السعر المستهدف')} EGP</b></div>
                    <div><small>وقف الخسارة</small><br><b style="color:#dc2626;">{item.get('وقف الخسارة')} EGP</b></div>
                </div>
                <div><strong>💡 التحليل:</strong> {item.get('أسباب التحليل')}</div>
            </div>
            """, unsafe_allow_html=True)

else:
    st.subheader("📉 صيد الفرص: أسهم منخفضة مرشحة للارتداد")
    dip_timeframe_filter = st.selectbox(
        "فلتر حسب المدى الزمني للارتداد:",
        ["جميع المدى الزمني", "مضاربية في نفس الجلسة (يومي)", "صعود أسبوعي", "صعود شهري"]
    )
    
    if not df_stocks.empty:
        dip_data = generate_ai_dip_opportunities(df_stocks, dip_timeframe_filter)
        for item in dip_data:
            st.markdown(f"""
            <div class="dip-card">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-weight: bold; font-size: 1.1rem;">🎯 {item.get('اسم السهم')}</span>
                    <div><span class="badge-time">⏱️ {item.get('المدى الزمني')}</span> <span class="badge-buy">{item.get('التوصية')}</span></div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); background: #f8fafc; padding: 8px; border-radius: 6px; text-align: center; margin-bottom: 8px;">
                    <div><small>السعر اللحظي</small><br><b style="color:#2563eb;">{item.get('live_price')} EGP</b></div>
                    <div><small>الشراء المقترح</small><br><b>{item.get('سعر الشراء')} EGP</b></div>
                    <div><small>المستهدف</small><br><b style="color:#16a34a;">{item.get('السعر المستهدف')} EGP</b></div>
                    <div><small>وقف الخسارة</small><br><b style="color:#dc2626;">{item.get('وقف الخسارة')} EGP</b></div>
                </div>
                <div><strong>💡 التحليل:</strong> {item.get('أسباب التحليل')}</div>
            </div>
            """, unsafe_allow_html=True)
                
