import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="محلل أسهم الشريعة الإسلامية - البورصة المصرية",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. تنسيق الواجهة ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        text-align: right;
    }

    [data-testid="collapsedControl"] { display: none !important; }

    .main-header { text-align: center; padding: 10px 0; color: #1e293b; }

    .stock-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }

    .stock-title { font-size: 1rem; font-weight: 700; color: #0f172a; }
    .stock-price { font-size: 1.15rem; font-weight: 700; color: #0f172a; }
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

    .badge-buy-strong { background-color: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
    .badge-buy { background-color: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
    .badge-watch { background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
    .badge-time { background-color: #f1f5f9; color: #475569; padding: 3px 8px; border-radius: 15px; font-size: 0.75rem; font-weight: 600; }
    .badge-score { background-color: #ede9fe; color: #5b21b6; padding: 3px 8px; border-radius: 15px; font-size: 0.75rem; font-weight: 700; }

    .disclaimer {
        background-color: #fef2f2;
        border-right: 4px solid #dc2626;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 0.82rem;
        color: #7f1d1d;
        margin-bottom: 14px;
    }

    .data-note {
        background-color: #f0f9ff;
        border-right: 4px solid #0284c7;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 0.8rem;
        color: #075985;
        margin-bottom: 14px;
    }

    .stButton > button { border-radius: 8px; font-weight: bold; background-color: #2563eb; color: white; }
</style>
""", unsafe_allow_html=True)

# --- 3. إعداد Gemini ---
def get_gemini_model():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ لم يتم العثور على GEMINI_API_KEY في Secrets أو متغيرات البيئة!")
        st.stop()
    genai.configure(api_key=api_key)
    for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']:
        try:
            return genai.GenerativeModel(model_name)
        except Exception:
            continue
    return genai.GenerativeModel('gemini-1.5-flash')

# --- 4. قائمة الأسهم المتوافقة مع الشريعة (ثابتة - لا تُعدّل) ---
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

# --- 5. جلب بيانات حقيقية فقط (بدون أي بيانات وهمية) ---
@st.cache_data(ttl=900, show_spinner=False)
def fetch_all_data():
    """
    يجلب بيانات حقيقية من yfinance فقط.
    أي سهم لا تتوفر له بيانات كافية يتم تجاهله تماماً (لا أرقام وهمية إطلاقاً).
    ملاحظة: بيانات yfinance للبورصة المصرية بها تأخير طبيعي (ليست لحظية بالثانية).
    """
    results = {}
    failed = []
    for name, symbol in SHARIAH_STOCKS.items():
        try:
            hist = yf.Ticker(symbol).history(period="4mo", interval="1d")
            # نحتاج بيانات كافية لحساب مؤشرات فنية حقيقية (SMA50, RSI14, ATR14)
            if hist.empty or len(hist) < 35:
                failed.append(name)
                continue
            results[name] = {"symbol": symbol.replace(".CA", ""), "hist": hist}
        except Exception:
            failed.append(name)
            continue
    return results, failed

# --- 6. حساب مؤشرات فنية حقيقية (بدون أي تدخل من الذكاء الاصطناعي) ---
def compute_indicators(hist: pd.DataFrame):
    close = hist['Close']
    high = hist['High']
    low = hist['Low']
    volume = hist['Volume']

    last_close = float(close.iloc[-1])
    prev_close = float(close.iloc[-2])
    day_change_pct = ((last_close - prev_close) / prev_close) * 100

    sma20 = float(close.rolling(20).mean().iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else float(close.rolling(len(close)).mean().iloc[-1])

    # RSI(14)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    rsi14 = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else 50.0

    # ATR(14) - لقياس التقلب الحقيقي لتحديد الهدف ووقف الخسارة
    prev_close_series = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close_series).abs(),
        (low - prev_close_series).abs()
    ], axis=1).max(axis=1)
    atr14 = float(tr.rolling(14).mean().iloc[-1])

    # الزخم
    momentum_5d = ((last_close - float(close.iloc[-6])) / float(close.iloc[-6])) * 100 if len(close) > 6 else 0.0
    momentum_20d = ((last_close - float(close.iloc[-21])) / float(close.iloc[-21])) * 100 if len(close) > 21 else 0.0

    # حجم التداول مقارنة بمتوسط 20 يوم
    avg_vol20 = float(volume.rolling(20).mean().iloc[-1])
    last_vol = float(volume.iloc[-1])
    vol_ratio = (last_vol / avg_vol20) if avg_vol20 > 0 else 1.0

    high_52w = float(high.max())
    low_52w = float(low.min())
    pct_from_high = ((last_close - high_52w) / high_52w) * 100

    return {
        "last_close": last_close,
        "day_change_pct": day_change_pct,
        "sma20": sma20,
        "sma50": sma50,
        "rsi14": rsi14,
        "atr14": atr14,
        "momentum_5d": momentum_5d,
        "momentum_20d": momentum_20d,
        "vol_ratio": vol_ratio,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "pct_from_high": pct_from_high,
    }

# --- 7. تسجيل نقاط الفرصة (منهج زخم كمي - نفس أسلوبك في التداول قصير المدى) ---
def score_opportunity(ind):
    score = 0
    tags = []

    # الاتجاه العام
    if ind["last_close"] > ind["sma20"] > ind["sma50"]:
        score += 3
        tags.append("اتجاه صاعد مؤكد (فوق المتوسطين)")
    elif ind["last_close"] > ind["sma20"]:
        score += 1
        tags.append("فوق المتوسط قصير المدى")

    # الزخم
    if ind["momentum_5d"] > 4:
        score += 2
        tags.append("زخم قوي خلال 5 جلسات")
    elif ind["momentum_5d"] > 1:
        score += 1
        tags.append("زخم إيجابي قصير المدى")

    # RSI - منطقة صحية (لا تشبع شرائي مبالغ فيه)
    if 50 <= ind["rsi14"] <= 68:
        score += 2
        tags.append(f"RSI في منطقة صحية ({ind['rsi14']:.0f})")
    elif 40 <= ind["rsi14"] < 50:
        score += 1
    elif ind["rsi14"] > 75:
        score -= 2
        tags.append(f"تشبع شرائي مرتفع ({ind['rsi14']:.0f}) - حذر")
    elif ind["rsi14"] < 30:
        tags.append(f"تشبع بيعي ({ind['rsi14']:.0f}) - احتمال ارتداد")

    # حجم التداول (تأكيد الحركة)
    if ind["vol_ratio"] > 1.8:
        score += 2
        tags.append(f"سيولة استثنائية ({ind['vol_ratio']:.1f}x المتوسط)")
    elif ind["vol_ratio"] > 1.3:
        score += 1
        tags.append(f"سيولة أعلى من المعتاد ({ind['vol_ratio']:.1f}x)")

    # القرب من القمة
    if ind["pct_from_high"] > -8:
        score += 1
        tags.append("قريب من أعلى مستوياته")

    return score, tags

def classify_timeframe(ind, score):
    if ind["vol_ratio"] > 1.7 and ind["momentum_5d"] > 3:
        return "مضاربة يومية"
    if ind["momentum_20d"] > 8 and ind["last_close"] > ind["sma50"]:
        return "صعود شهري (استثماري قصير)"
    return "صعود أسبوعي"

# --- 8. توليد الشرح بالذكاء الاصطناعي (يشرح الأرقام الحقيقية فقط، لا يخترع بيانات) ---
def generate_ai_explanation(candidates):
    """
    candidates: list of dicts بمؤشرات حقيقية محسوبة مسبقاً.
    الذكاء الاصطناعي هنا لا يولّد أي رقم؛ فقط يشرح الأرقام المعطاة بأسلوب محلل محترف.
    """
    model = get_gemini_model()

    payload = []
    for c in candidates:
        payload.append({
            "اسم السهم": c["name"],
            "السعر الحالي": round(c["ind"]["last_close"], 2),
            "التغير اليومي %": round(c["ind"]["day_change_pct"], 2),
            "الزخم 5 أيام %": round(c["ind"]["momentum_5d"], 2),
            "الزخم 20 يوم %": round(c["ind"]["momentum_20d"], 2),
            "RSI": round(c["ind"]["rsi14"], 1),
            "نسبة السيولة عن المتوسط": round(c["ind"]["vol_ratio"], 2),
            "النقاط الفنية": c["score"],
            "المدى الزمني المقترح": c["timeframe"],
            "ملاحظات فنية محسوبة": c["tags"],
        })

    prompt = f"""
أنت محلل فني محترف في البورصة المصرية (EGX). لديك بيانات فنية حقيقية محسوبة مسبقاً (وليست من عندك) لمجموعة أسهم.
مهمتك فقط: اكتب سبباً فنياً موجزاً (2-3 جمل) لكل سهم يشرح لماذا يُعتبر فرصة، بالاعتماد حصرياً على الأرقام المعطاة لك أدناه.

قواعد صارمة:
- ممنوع اختراع أي رقم (سعر، نسبة، تاريخ) غير موجود في البيانات المعطاة.
- لا تذكر أي أخبار أو أحداث لأنه ليس لديك بيانات عنها.
- أرجع النتيجة بصيغة JSON فقط، قائمة بالشكل التالي، بنفس ترتيب الأسهم المعطاة:
[
  {{"اسم السهم": "...", "الشرح": "..."}}
]

البيانات:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        parsed = json.loads(text)
        explanation_map = {item["اسم السهم"]: item["الشرح"] for item in parsed}
        return explanation_map
    except Exception:
        # fallback نصي مبني على نفس الأرقام الحقيقية (وليس بيانات وهمية جديدة)
        explanation_map = {}
        for c in candidates:
            ind = c["ind"]
            explanation_map[c["name"]] = (
                f"السهم فوق متوسطه المتحرك لـ 20 يوم بزخم {ind['momentum_5d']:.1f}% خلال آخر 5 جلسات، "
                f"ومؤشر القوة النسبية RSI عند {ind['rsi14']:.0f}، مع سيولة تعادل {ind['vol_ratio']:.1f}x المتوسط الشهري."
            )
        return explanation_map

# --- واجهة التطبيق ---
st.markdown('<h1 class="main-header">📈 أسهم الشريعة الإسلامية - البورصة المصرية</h1>', unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer">
⚠️ هذا التطبيق أداة مساعدة للتحليل الفني فقط وليس توصية استثمارية مضمونة. البيانات مصدرها Yahoo Finance وقد تحمل تأخيراً عن اللحظة الفعلية (غالباً 15-20 دقيقة). تحقق دائماً من السعر اللحظي عبر تطبيق الوساطة الخاص بك قبل تنفيذ أي صفقة.
</div>
""", unsafe_allow_html=True)

col_info, col_btn = st.columns([3, 1])
with col_info:
    st.write("تحليل فني كمي حقيقي (اتجاه، زخم، RSI، سيولة) لقائمتك المتوافقة مع الشريعة، مع شرح بالذكاء الاصطناعي للأرقام المحسوبة.")
with col_btn:
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with st.spinner("جاري جلب بيانات حقيقية وحساب المؤشرات الفنية..."):
    stocks_data, failed_stocks = fetch_all_data()

st.markdown(f"""
<div class="data-note">
📊 تم تحليل <strong>{len(stocks_data)}</strong> سهماً من أصل {len(SHARIAH_STOCKS)} ببيانات حقيقية فعلية.
{f"⚠️ {len(failed_stocks)} سهم لا تتوفر له بيانات كافية على Yahoo Finance حالياً فتم استبعاده (لا بيانات وهمية)." if failed_stocks else ""}
</div>
""", unsafe_allow_html=True)

if not stocks_data:
    st.error("تعذر جلب أي بيانات حقيقية حالياً. حاول التحديث بعد قليل.")
    st.stop()

# حساب المؤشرات والنقاط لكل الأسهم
analyzed = []
for name, data in stocks_data.items():
    ind = compute_indicators(data["hist"])
    score, tags = score_opportunity(ind)
    timeframe = classify_timeframe(ind, score)
    analyzed.append({
        "name": name,
        "symbol": data["symbol"],
        "ind": ind,
        "score": score,
        "tags": tags,
        "timeframe": timeframe,
    })

df_display = pd.DataFrame([{
    "name": a["name"], "symbol": a["symbol"],
    "price": a["ind"]["last_close"], "pct_change": a["ind"]["day_change_pct"],
    "high": a["ind"]["high_52w"], "low": a["ind"]["low_52w"]
} for a in analyzed])

# 1. أكثر 5 أسهم ارتفاعاً (بيانات حقيقية فقط)
st.subheader("🔥 أكثر 5 أسهم ارتفاعاً اليوم في قائمتك")
top_gainers = df_display.sort_values(by="pct_change", ascending=False).head(5)
for _, item in top_gainers.iterrows():
    change_class = "price-up" if item['pct_change'] >= 0 else "price-down"
    sign = "+" if item['pct_change'] >= 0 else ""
    st.markdown(f"""
    <div class="stock-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="stock-title">{item['name']} <small style="color:#64748b;">({item['symbol']})</small></span>
            <span class="{change_class}">{sign}{item['pct_change']:.2f}%</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
            <span class="stock-price">{item['price']:.2f} EGP</span>
            <span style="font-size: 0.8rem; color: #64748b;">أعلى 4 أشهر: {item['high']:.2f} | أقل 4 أشهر: {item['low']:.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 2. أفضل الفرص - مرتبة حسب النقاط الفنية الحقيقية
col_opp_title, col_filter = st.columns([2, 2])
with col_opp_title:
    st.subheader("🌟 أفضل الفرص الاستثمارية (تحليل فني كمي)")
with col_filter:
    timeframe_filter = st.selectbox(
        "فلتر حسب المدى الزمني للفرصة:",
        ["جميع المدى الزمني", "مضاربة يومية", "صعود أسبوعي", "صعود شهري (استثماري قصير)"],
        label_visibility="collapsed"
    )

candidates = [a for a in analyzed if a["score"] >= 4]
if timeframe_filter != "جميع المدى الزمني":
    candidates = [a for a in candidates if a["timeframe"] == timeframe_filter]
candidates.sort(key=lambda x: x["score"], reverse=True)
candidates = candidates[:8]

if not candidates:
    st.info("لا توجد حالياً أسهم تحقق شروط فرصة قوية (نقاط ≥ 4) ضمن هذا الفلتر. جرّب فلتر آخر أو حدّث البيانات لاحقاً.")
else:
    with st.spinner("جاري توليد الشرح الفني بالذكاء الاصطناعي..."):
        explanations = generate_ai_explanation(candidates)

    for c in candidates:
        ind = c["ind"]
        entry = ind["last_close"]
        target = entry + (2 * ind["atr14"])
        stop = entry - (1 * ind["atr14"])

        if c["score"] >= 7:
            rec, badge_class, border_color = "شراء قوي", "badge-buy-strong", "#16a34a"
        else:
            rec, badge_class, border_color = "شراء", "badge-buy", "#2563eb"

        reason = explanations.get(c["name"], " | ".join(c["tags"]))

        st.markdown(f"""
        <div class="opp-card" style="border-right-color: {border_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 6px;">
                <span style="font-size: 1.15rem; font-weight: bold; color: #0f172a;">🎯 {c['name']}</span>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span class="badge-score">⭐ {c['score']} نقطة</span>
                    <span class="badge-
