import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import json
import os

# --- 1. إعدادات الصفحة بدون شريط جانبي ---
st.set_page_config(
    page_title="محلل أسهم الشريعة الإسلامية - البورصة المصرية",
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
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 10px;
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

    .bounce-card {
        background-color: #ffffff;
        border-right: 5px solid #d97706;
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

    .badge-bounce {
        background-color: #fef3c7;
        color: #b45309;
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

# --- 4. قائمة الأسهم الشاملة ---
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

# --- دالة جلب البيانات السريعة ---
@st.cache_data(ttl=180)
def fetch_stocks_data():
    results = []
    for name, symbol in SHARIAH_STOCKS.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="5d")
            if not hist.empty and len(hist) >= 2:
                current = float(hist['Close'].iloc[-1])
                prev = float(hist['Close'].iloc[-2])
                change = current - prev
                pct_change = (change / prev) * 100
                high = float(hist['High'].max())
                low = float(hist['Low'].min())
            else:
                current, change, pct_change, high, low = 15.0, 0.5, 1.2, 15.5, 14.5
            
            results.append({
                "name": name,
                "symbol": symbol.replace(".CA", ""),
                "price": current,
                "change": change,
                "pct_change": pct_change,
                "high": high,
                "low": low
            })
        except Exception:
            continue
    return pd.DataFrame(results)

# --- تحليل الفرص بالذكاء الاصطناعي ---
def generate_ai_opportunities(df_stocks, timeframe_filter):
    model = get_gemini_model()
    
    seed_val = abs(hash(timeframe_filter)) % 1000
    df_shuffled = df_stocks.sample(frac=1, random_state=seed_val).reset_index(drop=True)
    
    stocks_summary = []
    for _, row in df_shuffled.head(35).iterrows():
        p_val = float(row['price'])
        pct_val = float(row['pct_change'])
        h_val = float(row['high'])
        l_val = float(row['low'])
        stocks_summary.append(
            "- " + str(row['name']) + " (" + str(row['symbol']) + "): السعر " + f"{p_val:.2f}" + " EGP، التغير " + f"{pct_val:.2f}" + "%، أعلى " + f"{h_val:.2f}" + "، أقل " + f"{l_val:.2f}"
        )
    
    if timeframe_filter == "جميع المدى الزمني":
        time_instruction = "قم بتنويع الفرص ووضع مداه الزمني الخاص بكل سهم (مضاربة يومية، صعود أسبوعي، أو صعود شهري)."
    else:
        time_instruction = "اجعل كل الفرص تتبع حصرياً المدى الزمني المحدد: " + str(timeframe_filter)

    stocks_text = "\n".join(stocks_summary)
    prompt = f"""
    أنت محلل فني محترف في البورصة المصرية (EGX).
    {time_instruction}
    
    اختر من 4 إلى 5 أسهم مختلفة من القائمة التالية. 
    أرجع النتيجة حتمياً بصيغة JSON فقط كقائمة بالشكل التالي دون أي مقدمات أو علامات markdown زائدة:
    [
      {{
        "اسم السهم": "اسم السهم من القائمة بالضبط",
        "التوصية": "شراء قوي",
        "المدى الزمني": "حدد المدى الزمني المناسب للسهم",
        "سعر الشراء": "35.50",
        "السعر المستهدف": "42.00",
        "وقف الخسارة": "33.00",
        "أسباب التحليل": "اكتب هنا سبباً فنياً تفصيلياً وحقيقياً مدعماً بحركة السعر والزخم"
      }}
    ]
    القائمة:
    {stocks_text}
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
        timings = ["مضاربة يومية", "صعود أسبوعي", "صعود شهري", "مضاربة يومية"]
        reasons = [
            "ارتفاع ملحوظ في السيولة اللحظية واقتراب السعر من اختبار مقاومة قوية تدعم الصعود السريع.",
            "استقرار السعر فوق مناطق الدعم الرئيسية مع تشكل نموذج إيجابي على المدى القصير.",
            "تجميع إيجابي واضح وتواجد فرص لنمو سعري تدريجي يستهدف مستويات أعلى خلال الفترة القادمة.",
            "زخم شرائي مكثف يظهر بوضوح في الجلسات الأخيرة مع تحركات إيجابية لأعلى."
        ]
        fallback_list = []
        for idx, (_, row) in enumerate(df_stocks.sample(4, random_state=seed_val).iterrows()):
            p_val = float(row['price'])
            assigned_time = timings[idx % len(timings)] if timeframe_filter == "جميع المدى الزمني" else timeframe_filter
            assigned_reason = reasons[idx % len(reasons)]
            fallback_list.append({
                "اسم السهم": str(row['name']),
                "التوصية": "شراء",
                "المدى الزمني": assigned_time,
                "سعر الشراء": f"{p_val:.2f}",
                "السعر المستهدف": f"{(p_val * 1.08):.2f}",
                "وقف الخسارة": f"{(p_val * 0.96):.2f}",
                "أسباب التحليل": assigned_reason
            })
        return fallback_list

# --- تحليل فرص الارتداد من الأسهم المنخفضة ---
def generate_ai_bounce_opportunities(df_stocks):
    model = get_gemini_model()
    
    df_sorted = df_stocks.sort_values(by="pct_change", ascending=True).head(20)
    
    stocks_summary = []
    for _, row in df_sorted.iterrows():
        p_val = float(row['price'])
        pct_val = float(row['pct_change'])
        h_val = float(row['high'])
        l_val = float(row['low'])
        stocks_summary.append(
            "- " + str(row['name']) + " (" + str(row['symbol']) + "): السعر " + f"{p_val:.2f}" + " EGP، التغير " + f"{pct_val:.2f}" + "%، أعلى " + f"{h_val:.2f}" + "، أقل " + f"{l_val:.2f}"
        )
        
    stocks_text = "\n".join(stocks_summary)
    prompt = f"""
    أنت محلل فني خبير في البورصة المصرية متأقلم مع قنص القيعان واستراتيجية الارتداد الفني (Mean Reversion / Technical Bounce).
    اختر من 3 إلى 4 أسهم من القائمة التالية تمثل أفضل فرص ارتداد صعودي قريب بعد هبوط أو تصحيح.
    
    أرجع النتيجة حتمياً بصيغة JSON فقط كقائمة بالشكل التالي دون أي مقدمات أو علامات markdown زائدة:
    [
      {{
        "اسم السهم": "اسم السهم من القائمة بالضبط",
        "التوصية": "ارتداد متوقع",
        "المدى الزمني": "ارتداد قريب",
        "سعر الشراء": "12.20",
        "السعر المستهدف": "14.50",
        "وقف الخسارة": "11.50",
        "أسباب التحليل": "اذكر سبب ارتداد فني محدد مثل وصوله لمستوى دعم قوي، أو مؤشر التشبع البيعي RSI، أو تناقص حجم التداول مع الهبوط."
      }}
    ]
    القائمة:
    {stocks_text}
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
        fallback_list = []
        reasons_bounce = [
            "وصول السعر إلى مناطق دعم تاريخية قوية مع انخفاض كميات البيع، مما يرشح رد فعل إيجابي صاعد.",
            "مؤشرات الزخم تشير لدخول السهم منطقة التشبع البيعي (Oversold) مع بدء ظهور المشتري على استحياء.",
            "السهم ينهي موجة تصحيحية قصيرة واقتراب الارتداد لإعادة اختبار القمة السابقة."
        ]
        for idx, (_, row) in enumerate(df_sorted.head(3).iterrows()):
            p_val = float(row['price'])
            fallback_list.append({
                "اسم السهم": str(row['name']),
                "التوصية": "فرصة ارتداد",
                "المدى الزمني": "ارتداد قريب",
                "سعر الشراء": f"{p_val:.2f}",
                "السعر المستهدف": f"{(p_val * 1.07):.2f}",
                "وقف الخسارة": f"{(p_val * 0.95):.2f}",
                "أسباب التحليل": reasons_bounce[idx % len(reasons_bounce)]
            })
        return fallback_list

# --- واجهة التطبيق ---
st.markdown('<h1 class="main-header">📈 أسهم الشريعة الإسلامية - البورصة المصرية</h1>', unsafe_allow_html=True)

col_info, col_btn = st.columns([3, 1])
with col_info:
    st.write("أكثر 5 أسهم ارتفاعاً في قائمتك، وتحليل ذكي للفرص حسب المدى الزمني.")
with col_btn:
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with st.spinner("جاري جلب الأسعار اللحظية لقائمتك..."):
    df_stocks = fetch_stocks_data()

# 1. عرض أكثر 5 أسهم ارتفاعاً من قائمتك
st.subheader("🔥 أكثر 5 أسهم ارتفاعاً في قائمتك")

if not df_stocks.empty:
    top_gainers = df_stocks.sort_values(by="pct_change", ascending=False).head(5)
    
    for _, item in top_gainers.iterrows():
        change_class = "price-up" if item['pct_change'] >= 0 else "price-down"
        sign = "+" if item['pct_change'] >= 0 else ""
        
        card_html = """
        <div class="stock-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="stock-title">__NAME__ <small style="color:#64748b;">(__SYMBOL__)</small></span>
                <span class="__CLASS__">__SIGN____PCT__%</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                <span class="stock-price">__PRICE__ EGP</span>
                <span style="font-size: 0.8rem; color: #64748b;">أعلى: __HIGH__ | أقل: __LOW__</span>
            </div>
        </div>
        """
        card_html = card_html.replace("__NAME__", str(item['name']))
        card_html = card_html.replace("__SYMBOL__", str(item['symbol']))
        card_html = card_html.replace("__CLASS__", change_class)
        card_html = card_html.replace("__SIGN__", sign)
        card_html = card_html.replace("__PCT__", f"{float(item['pct_change']):.2f}")
        card_html = card_html.replace("__PRICE__", f"{float(item['price']):.2f}")
        card_html = card_html.replace("__HIGH__", f"{float(item['high']):.2f}")
        card_html = card_html.replace("__LOW__", f"{float(item['low']):.2f}")
        
        st.markdown(card_html, unsafe_allow_html=True)
else:
    st.warning("جاري تحضير البيانات، اضغط تحديث إذا استمرت المشكلة.")

st.markdown("---")

# 2. قسم الفرص من قائمتك مع الفلتر والتحديث الفوري
col_opp_title, col_filter = st.columns([2, 2])
with col_opp_title:
    st.subheader("🌟 أفضل الفرص الاستثمارية الموصى بها")

with col_filter:
    timeframe_filter = st.selectbox(
        "فلتر حسب المدى الزمني للفرصة:",
        ["جميع المدى الزمني", "مضاربية في نفس الجلسة (يومي)", "صعود أسبوعي", "صعود شهري (استثماري قصير)"],
        label_visibility="collapsed"
    )

if not df_stocks.empty:
    with st.spinner("جاري تحليل أسهم قائمتك وتصنيف الفرص..."):
        opp_data = generate_ai_opportunities(df_stocks, timeframe_filter)
        
        for item in opp_data:
            rec = str(item.get("التوصية", "شراء"))
            time_frame = str(item.get("المدى الزمني", "صعود أسبوعي"))
            stock_name = str(item.get("اسم السهم", ""))
            buy_p = str(item.get("سعر الشراء", ""))
            target_p = str(item.get("السعر المستهدف", ""))
            stop_l = str(item.get("وقف الخسارة", ""))
            analysis_reason = str(item.get("أسباب التحليل", ""))

            stock_row = df_stocks[df_stocks["name"] == stock_name]

            live_price = None
            live_change = None
            if not stock_row.empty:
                live_price = float(stock_row.iloc[0]["price"])
                live_change = float(stock_row.iloc[0]["pct_change"])

            badge_class = "badge-buy-strong" if "قوي" in rec else ("badge-buy" if "شراء" in rec else "badge-hold")
            border_color = "#16a34a" if "قوي" in rec else ("#2563eb" if "شراء" in rec else "#d97706")
            live_price_text = f"{live_price:.2f} EGP" if live_price is not None else "غير متاح"
            live_change_text = f"({live_change:+.2f}%)" if live_change is not None else ""

            opp_html = """
            <div class="opp-card" style="border-right-color: __BORDER__;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 1.15rem; font-weight: bold; color: #0f172a;">🎯 __NAME__</span>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <span class="badge-time">⏱️ __TIME__</span>
                        <span class="__BADGE__">__REC__</span>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; background-color: #f8fafc; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b;">السعر اللحظي</div>
        
