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
    "سيدي كرير للبتروكيماويات": "SKPC.CA",
    # --- الأسهم دي جزء من مكونات مؤشر EGX 33 Shariah الرسمي (شركات كبيرة وسيولة عالية) وكانت ناقصة من القائمة الأصلية ---
    "المصرية للاتصالات": "ETEL.CA",
    "السويدي إليكتريك": "SWDY.CA",
    "طلعت مصطفى القابضة": "TMGH.CA",
    "بالم هيلز للتعمير": "PHDC.CA",
    "سوديك": "OCDI.CA",
    "جي بي أوتو": "AUTO.CA",
    "فوري لتكنولوجيا البنوك والمدفوعات الإلكترونية": "FWRY.CA",
    "ابن سينا فارما": "ISPH.CA",
    "النساجون الشرقيون": "ORWE.CA",
    "مدينة نصر للإسكان والتعمير": "MNHD.CA",
    "أوراسكوم للإنشاءات": "ORAS.CA",
    "أوراسكوم للتنمية": "ORHD.CA",
    "إعمار مصر للتنمية": "EMFD.CA",
    "عبور لاند للصناعات الغذائية": "OLFI.CA",
    "أبو قير للأسمدة والصناعات الكيماوية": "ABUK.CA",
    "راية القابضة": "RAYA.CA",
    "راية لخدمات مراكز الاتصال": "RACC.CA",
    "تعليم لخدمات الإدارة": "TAMD.CA",
    "ايجيترانس (مصر لخدمات النقل)": "ETRS.CA",
    "العربية لحليج الأقطان": "ACGC.CA",
    "العز للسيراميك والبورسلين (الجوهرة)": "ECAP.CA",
    "بنك فيصل الإسلامي المصري - بالجنيه": "FAIT.CA"
}

# --- 5. جلب بيانات حقيقية فقط (بدون أي بيانات وهمية) ---
@st.cache_data(ttl=900, show_spinner=False)
def fetch_all_data():
    """
    يجلب بيانات حقيقية من yfinance فقط (سنة كاملة لدعم اختبار تاريخي أوسع وأكثر مصداقية).
    أي سهم لا تتوفر له بيانات كافية يتم تجاهله تماماً (لا أرقام وهمية إطلاقاً).
    ملاحظة: بيانات yfinance للبورصة المصرية بها تأخير طبيعي (ليست لحظية بالثانية).
    """
    results = {}
    failed = []
    for name, symbol in SHARIAH_STOCKS.items():
        try:
            hist = yf.Ticker(symbol).history(period="2y", interval="1d")
            # نحتاج بيانات كافية لحساب مؤشرات فنية حقيقية (SMA50, RSI14, ATR14)
            if hist.empty or len(hist) < 60:
                failed.append(name)
                continue
            results[name] = {"symbol": symbol.replace(".CA", ""), "hist": hist}
        except Exception:
            failed.append(name)
            continue
    return results, failed

@st.cache_data(ttl=900, show_spinner=False)
def fetch_market_trend():
    """اتجاه المؤشر العام للبورصة المصرية (EGX30) + نظام التقلب الحالي (يوجّه لأي استراتيجية أنسب الآن)."""
    try:
        hist = yf.Ticker("^CASE30").history(period="6mo", interval="1d")
        if hist.empty or len(hist) < 55:
            return None
        ind = compute_indicators(hist)
        if ind["last_close"] > ind["sma20"] > ind["sma50"]:
            trend = {"label": "📈 صاعد", "color": "#16a34a"}
        elif ind["last_close"] < ind["sma20"] < ind["sma50"]:
            trend = {"label": "📉 هابط", "color": "#dc2626"}
        else:
            trend = {"label": "↔️ متذبذب", "color": "#d97706"}

        # نظام التقلب: نقارن ATR% الحالي بمتوسطه التاريخي لنفس المؤشر خلال آخر 6 شهور
        close = hist["Close"]
        high = hist["High"]
        low = hist["Low"]
        prev_close = close.shift(1)
        tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
        atr_pct_series = (tr.rolling(14).mean() / close) * 100
        current_atr_pct = float(atr_pct_series.iloc[-1])
        median_atr_pct = float(atr_pct_series.median())

        if current_atr_pct > median_atr_pct * 1.2:
            regime = {"label": "🌪️ تقلب مرتفع", "hint": "فرص الارتداد قد تكون أنسب في هذا النظام (وفق دراسات على أسواق مشابهة)", "color": "#d97706"}
        elif current_atr_pct < median_atr_pct * 0.8:
            regime = {"label": "😌 تقلب منخفض", "hint": "استراتيجية الزخم قد تكون أنسب في هذا النظام", "color": "#16a34a"}
        else:
            regime = {"label": "⚖️ تقلب معتدل", "hint": "لا تفضيل واضح بين الاستراتيجيتين حالياً", "color": "#64748b"}

        return {"label": trend["label"], "color": trend["color"], "ind": ind, "regime": regime}
    except Exception:
        return None

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
    avg_daily_value = avg_vol20 * last_close  # متوسط قيمة التداول اليومي بالجنيه - لقياس السيولة الحقيقية

    # تأكيد الاتجاه على المدى الأسبوعي (multi-timeframe) - يقلل إشارات الاتجاه اليومي المضللة
    weekly_confirmed = False
    try:
        weekly_close = close.resample("W").last().dropna()
        if len(weekly_close) >= 5:
            wma4 = weekly_close.rolling(4).mean().iloc[-1]
            weekly_confirmed = bool(weekly_close.iloc[-1] > wma4)
    except Exception:
        weekly_confirmed = False

    # ADX(14) - قوة الاتجاه (يفرّق بين اتجاه قوي حقيقي وتذبذب عشوائي)
    try:
        up_move = high.diff()
        down_move = -low.diff()
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
        tr_smooth = tr.rolling(14).mean()
        plus_di = 100 * (plus_dm.rolling(14).mean() / tr_smooth.replace(0, np.nan))
        minus_di = 100 * (minus_dm.rolling(14).mean() / tr_smooth.replace(0, np.nan))
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx_val = dx.rolling(14).mean().iloc[-1]
        adx14 = float(adx_val) if not np.isnan(adx_val) else 20.0
    except Exception:
        adx14 = 20.0

    return {
        "last_close": last_close,
        "day_change_pct": day_change_pct,
        "sma20": sma20,
        "sma50": sma50,
        "rsi14": rsi14,
        "atr14": atr14,
        "adx14": adx14,
        "momentum_5d": momentum_5d,
        "momentum_20d": momentum_20d,
        "vol_ratio": vol_ratio,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "pct_from_high": pct_from_high,
        "avg_daily_value": avg_daily_value,
        "weekly_confirmed": weekly_confirmed,
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

    # تأكيد على المدى الأسبوعي (multi-timeframe)
    if ind.get("weekly_confirmed"):
        score += 1
        tags.append("الاتجاه الأسبوعي يؤكد الصعود")

    # قوة الاتجاه (ADX) - يميّز بين اتجاه قوي حقيقي وتذبذب عشوائي بلا اتجاه
    if ind.get("adx14", 0) >= 25:
        score += 1
        tags.append(f"اتجاه قوي مؤكد (ADX {ind['adx14']:.0f})")
    elif ind.get("adx14", 0) < 15:
        tags.append(f"اتجاه ضعيف/تذبذب (ADX {ind['adx14']:.0f}) - حذر من إشارات كاذبة")

    return score, tags

def classify_timeframe(ind, score):
    if ind["vol_ratio"] > 1.7 and ind["momentum_5d"] > 3:
        return "مضاربة يومية"
    if ind["momentum_20d"] > 8 and ind["last_close"] > ind["sma50"]:
        return "صعود شهري (استثماري قصير)"
    return "صعود أسبوعي"

# --- 7.3 استراتيجية مختلفة تماماً: فرص ارتداد من تشبع بيعي (Mean Reversion) - مخاطرة أعلى ---
def score_reversal_opportunity(ind):
    """
    عكس منطق score_opportunity تماماً: هنا نبحث عمداً عن أسهم منخفضة تظهر بوادر ارتداد مبكرة،
    وليس أسهماً في اتجاه صاعد مؤكد. هذه الفئة أعلى مخاطرة لأن الانخفاض قد يستمر (falling knife).
    """
    score = 0
    tags = []
    if ind["rsi14"] < 35:
        score += 2
        tags.append(f"تشبع بيعي واضح (RSI {ind['rsi14']:.0f})")
    elif ind["rsi14"] < 45:
        score += 1
        tags.append(f"اقتراب من منطقة التشبع البيعي (RSI {ind['rsi14']:.0f})")
    if ind["pct_from_high"] < -20:
        score += 1
        tags.append(f"منخفض {abs(ind['pct_from_high']):.0f}% عن أعلى قمة خلال الفترة")
    if ind["momentum_5d"] > 1:
        score += 2
        tags.append("بوادر ارتداد: زخم إيجابي خلال آخر 5 جلسات رغم الاتجاه الهابط العام")
    if ind["vol_ratio"] > 1.5:
        score += 1
        tags.append(f"سيولة مرتفعة مصاحبة للارتداد المحتمل ({ind['vol_ratio']:.1f}x)")
    if ind["last_close"] > ind["sma20"]:
        score += 1
        tags.append("عاد فوق المتوسط قصير المدى - إشارة تأكيد أولى")
    return score, tags

# --- 7.4 التحليل الأساسي (Fundamentals) - بيانات حقيقية من yfinance، تُتجاهل بأمان لو غير متوفرة ---
@st.cache_data(ttl=86400, show_spinner=False)
def fetch_fundamentals(symbol):
    """
    يجلب مؤشرات أساسية حقيقية فقط. أسهم كثيرة صغيرة في EGX قد لا تتوفر لها هذه البيانات
    على Yahoo Finance، وفي هذه الحالة يتم تجاهل البُعد الأساسي بأمان (لا أرقام وهمية).
    """
    try:
        info = yf.Ticker(symbol).info
        pe = info.get("trailingPE")
        roe = info.get("returnOnEquity")
        debt_to_equity = info.get("debtToEquity")
        profit_margin = info.get("profitMargins")
        sector = info.get("sector") or "غير مصنّف"
        available = any(v is not None for v in [pe, roe, debt_to_equity, profit_margin])
        return {
            "available": available,
            "pe": pe,
            "roe": roe,
            "debt_to_equity": debt_to_equity,
            "profit_margin": profit_margin,
            "sector": sector,
        }
    except Exception:
        return {"available": False, "pe": None, "roe": None, "debt_to_equity": None, "profit_margin": None, "sector": "غير مصنّف"}

def score_fundamentals(fund):
    if not fund["available"]:
        return 0, []
    score = 0
    tags = []
    if fund["pe"] is not None and fund["pe"] > 0:
        if fund["pe"] < 12:
            score += 2
            tags.append(f"تقييم رخيص نسبياً (P/E {fund['pe']:.1f})")
        elif fund["pe"] < 20:
            score += 1
            tags.append(f"تقييم معقول (P/E {fund['pe']:.1f})")
    if fund["roe"] is not None and fund["roe"] > 0.10:
        score += 1
        tags.append(f"عائد جيد على حقوق الملكية ({fund['roe']*100:.0f}%)")
    if fund["debt_to_equity"] is not None and fund["debt_to_equity"] < 100:
        score += 1
        tags.append("مديونية منخفضة نسبياً")
    if fund["profit_margin"] is not None and fund["profit_margin"] > 0.10:
        score += 1
        tags.append(f"هامش ربح صحي ({fund['profit_margin']*100:.0f}%)")
    return score, tags

# --- 7.5 اختبار تاريخي (Backtest) - يقيس أداء نفس القاعدة على بيانات حقيقية سابقة ---
def backtest_stock(hist, score_threshold, strategy="momentum", holding_days=10, atr_target_mult=2, atr_stop_mult=1, step=2):
    """
    يطبّق نفس منطق التسجيل (زخم أو ارتداد) على نقاط زمنية سابقة (بيانات حقيقية فقط)
    ويسجل هل كانت الصفقة الافتراضية ستحقق الهدف أم وقف الخسارة خلال holding_days.
    يستخدم نافذة متحركة ثابتة (150 يوم) بدل إعادة الحساب من بداية البيانات في كل مرة،
    للحفاظ على سرعة معقولة مع بيانات سنة كاملة. هذا ليس ضماناً للمستقبل، لكنه قياس صادق
    لأداء القاعدة على بيانات فعلية سابقة.
    """
    score_fn = score_opportunity if strategy == "momentum" else score_reversal_opportunity
    outcomes = []
    n = len(hist)
    if n < 60 + holding_days:
        return outcomes
    for i in range(50, n - holding_days, step):
        window = hist.iloc[max(0, i - 150): i + 1]
        try:
            ind = compute_indicators(window)
        except Exception:
            continue
        score, _ = score_fn(ind)
        if score < score_threshold:
            continue
        entry = ind["last_close"]
        target = entry + (atr_target_mult * ind["atr14"])
        stop = entry - (atr_stop_mult * ind["atr14"])
        future = hist.iloc[i + 1: i + 1 + holding_days]
        outcome, exit_price = None, None
        for _, row in future.iterrows():
            if row["High"] >= target:
                outcome, exit_price = "win", target
                break
            if row["Low"] <= stop:
                outcome, exit_price = "loss", stop
                break
        if outcome is None and len(future) > 0:
            exit_price = float(future["Close"].iloc[-1])
            outcome = "win" if exit_price > entry else "loss"
        if outcome:
            return_pct = ((exit_price - entry) / entry) * 100 if entry > 0 else 0
            outcomes.append({"outcome": outcome, "return_pct": return_pct})
    return outcomes

@st.cache_data(ttl=900, show_spinner=False)
def run_full_backtest(_stocks_data, score_threshold, strategy="momentum"):
    """يجمّع نتائج الـ backtest عبر كل الأسهم لعتبة نقاط معينة، مع مقاييس احترافية (Profit Factor)."""
    all_trades = []
    buy_hold_returns = []
    for name, data in _stocks_data.items():
        all_trades.extend(backtest_stock(data["hist"], score_threshold, strategy=strategy))
        close = data["hist"]["Close"]
        if len(close) > 1 and float(close.iloc[0]) > 0:
            buy_hold_returns.append(((float(close.iloc[-1]) - float(close.iloc[0])) / float(close.iloc[0])) * 100)

    wins = [t for t in all_trades if t["outcome"] == "win"]
    losses = [t for t in all_trades if t["outcome"] == "loss"]
    total = len(wins) + len(losses)
    win_rate = (len(wins) / total * 100) if total > 0 else None
    avg_win_pct = (sum(t["return_pct"] for t in wins) / len(wins)) if wins else None
    avg_loss_pct = (sum(t["return_pct"] for t in losses) / len(losses)) if losses else None
    gross_win = sum(t["return_pct"] for t in wins)
    gross_loss = abs(sum(t["return_pct"] for t in losses))
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else None
    avg_buy_hold = (sum(buy_hold_returns) / len(buy_hold_returns)) if buy_hold_returns else None

    return {
        "total": total, "wins": len(wins), "losses": len(losses), "win_rate": win_rate,
        "avg_win_pct": avg_win_pct, "avg_loss_pct": avg_loss_pct, "profit_factor": profit_factor,
        "avg_buy_hold": avg_buy_hold,
    }

# --- 7.6 تخزين عام (سجل التوصيات + قائمة المتابعة) - Google Sheets مع fallback لـ CSV محلي ---
# ملاحظة مهمة: ملف CSV المحلي بيتمسح كل مرة يتم فيها إعادة نشر (redeploy) التطبيق على
# Streamlit Cloud، لأن مساحة التخزين المحلية مؤقتة (ephemeral) مش دائمة.
# الحل: لو تم إعداد Google Sheets (راجع تعليمات الإعداد أسفل الصفحة)، البيانات هتتخزن هناك
# وهتفضل موجودة حتى بعد أي تحديث للكود. لو مفيش إعداد، هيرجع تلقائياً للتخزين المحلي بـ CSV
# (نفس السلوك القديم) عشان التطبيق يشتغل من غير ما يحصل أي خطأ.
LOG_PATH = "recommendations_log.csv"
EXEC_COL = "نُفّذت فعلاً؟"
NOTIFIED_COL = "تم التنبيه؟"
LOG_COLUMNS = ["التاريخ", "السهم", "الرمز", "سعر الدخول", "الهدف", "وقف الخسارة", "النقاط", "سبب الدخول", EXEC_COL, NOTIFIED_COL]

WATCHLIST_PATH = "watchlist.csv"
WATCHLIST_COLUMNS = ["السهم", "الرمز", "تاريخ الإضافة"]

USE_GSHEETS = ("gcp_service_account" in st.secrets) and ("GSHEET_URL" in st.secrets)
USE_TELEGRAM = ("TELEGRAM_BOT_TOKEN" in st.secrets) and ("TELEGRAM_CHAT_ID" in st.secrets)

@st.cache_resource(show_spinner=False)
def get_worksheet(tab_name, columns):
    """يفتح تبويب معين في الـ Google Sheet المحدد في الإعدادات (Secrets). يُنشئه لو مش موجود."""
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open_by_url(st.secrets["GSHEET_URL"])
    try:
        ws = sh.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=2000, cols=len(columns) + 2)
        ws.append_row(columns)
    return ws

def load_table(tab_name, columns, csv_path, bool_cols=None):
    """يحمّل جدول (سجل التوصيات أو قائمة المتابعة) من Google Sheets أو CSV محلي حسب المتاح."""
    bool_cols = bool_cols or []
    df = None
    if USE_GSHEETS:
        try:
            ws = get_worksheet(tab_name, columns)
            records = ws.get_all_records()
            df = pd.DataFrame(records) if records else pd.DataFrame(columns=columns)
        except Exception as e:
            st.warning(f"⚠️ تعذر الاتصال بـ Google Sheets ({tab_name}): {e} — سيتم استخدام تخزين محلي مؤقت بدلاً منه لهذه الجلسة.")
    if df is None:
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
            except Exception:
                df = pd.DataFrame(columns=columns)
        else:
            df = pd.DataFrame(columns=columns)
    for c in columns:
        if c not in df.columns:
            df[c] = ""
    for c in bool_cols:
        df[c] = df[c].apply(
            lambda v: str(v).strip().lower() in ("true", "1", "yes", "نعم") if pd.notna(v) and str(v).strip() != "" else False
        )
    return df[columns]

def write_table(df, tab_name, columns, csv_path):
    """يكتب نسخة كاملة من الجدول (سجل التوصيات أو قائمة المتابعة)."""
    df = df[columns]
    if USE_GSHEETS:
        try:
            ws = get_worksheet(tab_name, columns)
            ws.clear()
            ws.update([df.columns.values.tolist()] + df.astype(str).values.tolist())
            return True
        except Exception as e:
            st.error(f"⚠️ تعذر الحفظ في Google Sheets ({tab_name}): {e}")
            return False
    try:
        df.to_csv(csv_path, index=False)
        return True
    except Exception:
        return False

def load_log():
    return load_table("log", LOG_COLUMNS, LOG_PATH, bool_cols=[EXEC_COL, NOTIFIED_COL])

def write_full_log(df):
    return write_table(df, "log", LOG_COLUMNS, LOG_PATH)

def load_watchlist():
    return load_table("watchlist", WATCHLIST_COLUMNS, WATCHLIST_PATH)

def save_watchlist(df):
    return write_table(df, "watchlist", WATCHLIST_COLUMNS, WATCHLIST_PATH)

def append_to_log(candidates, reasons=None):
    reasons = reasons or {}
    log_df = load_log()
    today = datetime.now().strftime("%Y-%m-%d")
    new_rows = []
    for c in candidates:
        ind = c["ind"]
        already_logged = ((log_df["التاريخ"] == today) & (log_df["السهم"] == c["name"])).any() if not log_df.empty else False
        if already_logged:
            continue
        new_rows.append({
            "التاريخ": today,
            "السهم": c["name"],
            "الرمز": c["symbol"],
            "سعر الدخول": round(ind["last_close"], 2),
            "الهدف": round(ind["last_close"] + 2 * ind["atr14"], 2),
            "وقف الخسارة": round(ind["last_close"] - 1 * ind["atr14"], 2),
            "النقاط": c["total_score"],
            "سبب الدخول": reasons.get(c["name"], " | ".join(c["tags"]))[:200],
            EXEC_COL: False,
            NOTIFIED_COL: False,
        })
    if new_rows:
        log_df = pd.concat([log_df, pd.DataFrame(new_rows)], ignore_index=True)
        write_full_log(log_df)
    return log_df

def purge_old_entries(log_df, retention_days):
    """
    يشيل من العرض أي توصية أقدم من retention_days (افتراضياً حتى سنة) — التوصيات القديمة
    مش محتاجة تفضل متخزنة، فالتخزين هنا مؤقت بطبيعته وليس أرشيفاً دائماً.
    ده تصفية للعرض فقط؛ الحذف الفعلي من المصدر بيتم بزر "تنظيف السجل" تحت.
    """
    if log_df.empty:
        return log_df
    try:
        today = pd.Timestamp(datetime.now().date())
        dates = pd.to_datetime(log_df["التاريخ"], errors="coerce")
        keep_mask = (today - dates).dt.days <= retention_days
        return log_df[keep_mask.fillna(True)].reset_index(drop=True)
    except Exception:
        return log_df

def send_telegram_message(text):
    """يبعت رسالة تنبيه عبر بوت تليجرام (لو تم إعداد TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID في الـ Secrets)."""
    if not USE_TELEGRAM:
        return False
    try:
        import requests
        url = f"https://api.telegram.org/bot{st.secrets['TELEGRAM_BOT_TOKEN']}/sendMessage"
        requests.post(url, data={"chat_id": st.secrets["TELEGRAM_CHAT_ID"], "text": text}, timeout=10)
        return True
    except Exception:
        return False



def price_on_or_before(hist, target_date):
    """
    يرجع آخر سعر إغلاق فعلي متاح بتاريخ target_date أو قبله (من بيانات yfinance الحقيقية).
    نستخدم هذا بدل السعر الحالي عند تقييم توصية "انتهت مهلتها"، عشان الرقم يعكس
    فعلاً سعر السهم في تاريخ الاستحقاق، مش سعر النهاردة اللي ممكن يكون بعده بأيام.
    """
    if hist is None or hist.empty:
        return None
    try:
        idx = hist.index
        target = pd.Timestamp(target_date)
        if idx.tz is not None:
            target = target.tz_localize(idx.tz) if target.tzinfo is None else target.tz_convert(idx.tz)
        elif target.tzinfo is not None:
            target = target.tz_localize(None)
        eligible = hist.loc[idx <= target]
        if eligible.empty:
            return None
        return float(eligible["Close"].iloc[-1])
    except Exception:
        return None

def evaluate_log(log_df, current_prices: dict, stocks_data: dict, holding_days=15, capital_per_trade=10000.0):
    """
    يقيّم كل توصية مسجّلة:
    - لو وصلت الهدف أو ضربت الوقف (حسب السعر الحالي) -> النتيجة محسومة بسعر الهدف/الوقف.
    - لو عدّت المدة الزمنية المحددة (holding_days) من غير ما توصل لأي منهم -> "انتهت المهلة"،
      وبيتم تقييمها بسعر الإغلاق الفعلي التاريخي في تاريخ الاستحقاق (من نفس بيانات yfinance)،
      مش بالسعر الحالي، عشان الرقم يبقى دقيق حتى لو المستخدم فتح التطبيق بعد المهلة بأيام.
      لو السعر التاريخي مش متاح (السهم خرج من القائمة مثلاً) بيرجع تقدير تقريبي بالسعر الحالي مع توضيح ذلك.
    - غير كده -> لسه مفتوحة (تقييم لحظي غير محقق).
    وبيحسب لكل توصية نسبة العائد% والربح/الخسارة الافتراضي لو تم استثمار مبلغ ثابت (capital_per_trade) فيها.
    """
    if log_df.empty:
        return log_df
    log_df = log_df.copy()
    today = pd.Timestamp(datetime.now().date())

    statuses, exit_prices, days_elapsed_list, pct_returns, pnl_list = [], [], [], [], []
    pnl_col_name = f"الربح/الخسارة لو استثمرت {capital_per_trade:,.0f} جنيه"

    for _, row in log_df.iterrows():
        current = current_prices.get(row["السهم"])
        try:
            entry_date = pd.to_datetime(row["التاريخ"])
            days_elapsed = (today - entry_date).days
        except Exception:
            entry_date, days_elapsed = None, None

        try:
            entry_price = float(row["سعر الدخول"])
        except (ValueError, TypeError):
            entry_price = None

        try:
            target_price = float(row["الهدف"])
        except (ValueError, TypeError):
            target_price = None
        try:
            stop_price = float(row["وقف الخسارة"])
        except (ValueError, TypeError):
            stop_price = None

        if current is None:
            status, exit_price = "⏳ لا تتوفر بيانات حالية", None
        elif target_price is None or stop_price is None:
            status, exit_price = "⚠️ بيانات الهدف/الوقف غير صالحة", None
        elif current >= target_price:
            status, exit_price = "✅ تحقق الهدف", target_price
        elif current <= stop_price:
            status, exit_price = "❌ ضرب وقف الخسارة", stop_price
        elif days_elapsed is not None and days_elapsed >= holding_days:
            hist = stocks_data.get(row["السهم"], {}).get("hist")
            exit_date = entry_date + pd.Timedelta(days=holding_days)
            hist_price = price_on_or_before(hist, exit_date)
            if hist_price is not None:
                status, exit_price = "⏰ انتهت المهلة (سعر تاريخي فعلي)", hist_price
            else:
                status, exit_price = "⏰ انتهت المهلة (تقدير بالسعر الحالي)", current
        else:
            status, exit_price = "⏳ لسه مفتوحة", current

        pct_return, pnl = None, None
        if exit_price is not None and entry_price:
            pct_return = ((exit_price - entry_price) / entry_price) * 100
            pnl = (pct_return / 100) * capital_per_trade

        statuses.append(status)
        exit_prices.append(round(exit_price, 2) if exit_price is not None else None)
        days_elapsed_list.append(days_elapsed)
        pct_returns.append(round(pct_return, 2) if pct_return is not None else None)
        pnl_list.append(round(pnl, 2) if pnl is not None else None)

    log_df["الحالة الحالية"] = statuses
    log_df["أيام مرت"] = days_elapsed_list
    log_df["نسبة العائد %"] = pct_returns
    log_df[pnl_col_name] = pnl_list
    return log_df

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
    market_trend = fetch_market_trend()

if market_trend:
    st.markdown(f"""
    <div class="data-note" style="border-right-color:{market_trend['color']}; text-align:center; font-size:0.95rem;">
    السوق العام (مؤشر EGX30): <strong style="color:{market_trend['color']};">{market_trend['label']}</strong>
    | نظام التقلب: <strong style="color:{market_trend['regime']['color']};">{market_trend['regime']['label']}</strong>
    — {market_trend['regime']['hint']}
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div class="data-note">
📊 تم تحليل <strong>{len(stocks_data)}</strong> سهماً من أصل {len(SHARIAH_STOCKS)} ببيانات حقيقية فعلية.
{f"⚠️ {len(failed_stocks)} سهم لا تتوفر له بيانات كافية على Yahoo Finance حالياً فتم استبعاده (لا بيانات وهمية)." if failed_stocks else ""}
</div>
""", unsafe_allow_html=True)

if not stocks_data:
    st.error("تعذر جلب أي بيانات حقيقية حالياً. حاول التحديث بعد قليل.")
    st.stop()

# نحسب تاريخ آخر بيانات فعلياً متاحة (مش وقت فتحك للتطبيق) - عشان تعرف بالظبط البيانات ليوم إيه
from collections import Counter
_last_dates = [d["hist"].index[-1].date() for d in stocks_data.values() if not d["hist"].empty]
data_as_of_date = Counter(_last_dates).most_common(1)[0][0] if _last_dates else None
_days_old = (datetime.now().date() - data_as_of_date).days if data_as_of_date else None

if data_as_of_date:
    if _days_old is not None and _days_old >= 1:
        st.warning(f"⚠️ البيانات المعروضة هي **آخر جلسة تداول مؤكدة بتاريخ {data_as_of_date.strftime('%Y-%m-%d')}** (منذ {_days_old} يوم) — Yahoo Finance لسه ماحدّثش بيانات اليوم. **متعتمدش على الأسعار دي للتنفيذ الفعلي**، راجع سعر السوق اللحظي من تطبيق شركة الوساطة قبل أي قرار.")
    else:
        st.success(f"✅ البيانات المعروضة محدّثة لجلسة اليوم ({data_as_of_date.strftime('%Y-%m-%d')}).")

# حساب المؤشرات والنقاط لكل الأسهم
analyzed = []
for name, data in stocks_data.items():
    ind = compute_indicators(data["hist"])
    tech_score, tech_tags = score_opportunity(ind)
    reversal_score, reversal_tags = score_reversal_opportunity(ind)
    timeframe = classify_timeframe(ind, tech_score)
    fund = fetch_fundamentals(data["symbol"] + ".CA")
    fund_score, fund_tags = score_fundamentals(fund)

    # القوة النسبية مقابل السوق العام (Alpha) - هل السهم متفوق على أداء EGX30 نفسه؟
    alpha_score = 0
    alpha_tag = None
    if market_trend:
        alpha_20d = ind["momentum_20d"] - market_trend["ind"]["momentum_20d"]
        if alpha_20d > 3:
            alpha_score = 1
            alpha_tag = f"يتفوق على أداء السوق العام بـ {alpha_20d:.1f}% خلال 20 يوم"

    analyzed.append({
        "name": name,
        "symbol": data["symbol"],
        "ind": ind,
        "score": tech_score,             # النقاط الفنية فقط - نفس ما يُستخدم في الـ backtest
        "total_score": tech_score + fund_score + alpha_score,  # الإجمالي لعرض الأولوية
        "fund_score": fund_score,
        "fund": fund,
        "sector": fund.get("sector", "غير مصنّف"),
        "tags": tech_tags,
        "fund_tags": fund_tags,
        "alpha_tag": alpha_tag,
        "reversal_score": reversal_score,
        "reversal_tags": reversal_tags,
        "timeframe": timeframe,
    })

df_display = pd.DataFrame([{
    "name": a["name"], "symbol": a["symbol"],
    "price": a["ind"]["last_close"], "pct_change": a["ind"]["day_change_pct"],
    "high": a["ind"]["high_52w"], "low": a["ind"]["low_52w"]
} for a in analyzed])

# فلتر القطاع - عام على كل أقسام الفرص تحت (أفضل الفرص، الارتداد، الجودة الأساسية)
all_sectors = sorted(set(a["sector"] for a in analyzed if a["sector"] and a["sector"] != "غير مصنّف"))
sector_filter = st.selectbox("🏭 فلترة حسب القطاع (تُطبَّق على كل أقسام الفرص بالأسفل):", ["كل القطاعات"] + all_sectors)
if sector_filter != "كل القطاعات":
    analyzed_for_opps = [a for a in analyzed if a["sector"] == sector_filter]
else:
    analyzed_for_opps = analyzed

st.markdown("---")

# ⭐ قائمة المتابعة - أسهم يحددها المستخدم ليتابعها بانتظام (تُخزَّن مثل سجل التوصيات)
st.subheader("⭐ قائمة المتابعة")
watchlist_df = load_watchlist()
watch_names = set(watchlist_df["السهم"]) if not watchlist_df.empty else set()

with st.expander("➕ إدارة قائمة المتابعة"):
    all_names_sorted = sorted(a["name"] for a in analyzed)
    selected_watch = st.multiselect("اختر الأسهم اللي عايز تتابعها بانتظام", all_names_sorted, default=sorted(watch_names))
    if st.button("💾 حفظ قائمة المتابعة"):
        existing_dates = dict(zip(watchlist_df["السهم"], watchlist_df["تاريخ الإضافة"])) if not watchlist_df.empty else {}
        today_str = datetime.now().strftime("%Y-%m-%d")
        new_watch_rows = []
        for name in selected_watch:
            sym = next((a["symbol"] for a in analyzed if a["name"] == name), "")
            new_watch_rows.append({"السهم": name, "الرمز": sym, "تاريخ الإضافة": existing_dates.get(name, today_str)})
        new_watch_df = pd.DataFrame(new_watch_rows, columns=WATCHLIST_COLUMNS)
        if save_watchlist(new_watch_df):
            st.success("✅ اتحفظت قائمة المتابعة.")
            st.rerun()
    if not USE_GSHEETS:
        st.caption("💾 قائمة المتابعة حالياً مخزّنة مؤقتاً — اربط Google Sheets (تعليمات آخر الصفحة) عشان تفضل محفوظة.")

if watch_names:
    watch_analyzed = [a for a in analyzed if a["name"] in watch_names]
    for a in watch_analyzed:
        ind = a["ind"]
        chg_class = "price-up" if ind["day_change_pct"] >= 0 else "price-down"
        st.markdown(f"""
        <div class="stock-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="stock-title">{a['name']}</span>
                <span class="{chg_class}">{ind['day_change_pct']:+.2f}%</span>
            </div>
            <div style="font-size:0.85rem; color:#64748b; margin-top:4px;">
                {ind['last_close']:.2f} EGP | RSI {ind['rsi14']:.0f} | نقاط الفرصة: {a['score']} | نقاط الارتداد: {a['reversal_score']} | القطاع: {a['sector']}
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.caption("مفيش أسهم في قائمة المتابعة حالياً. افتح 'إدارة قائمة المتابعة' فوق عشان تضيف.")

st.markdown("---")

# 1. أكثر ارتفاعاً وأكثر انخفاضاً - مع فلتر المدة
st.subheader("📊 الأكثر حركة في قائمتك")
duration_choice = st.selectbox(
    "المدة:",
    ["يوم واحد", "أسبوع (5 جلسات)", "شهر (21 جلسة)", "سنة (252 جلسة)"],
    label_visibility="collapsed"
)
duration_days = {"يوم واحد": 1, "أسبوع (5 جلسات)": 5, "شهر (21 جلسة)": 21, "سنة (252 جلسة)": 252}[duration_choice]

def pct_change_over(hist, days):
    try:
        if len(hist) <= days:
            return None
        start_price = float(hist["Close"].iloc[-1 - days])
        end_price = float(hist["Close"].iloc[-1])
        if start_price <= 0:
            return None
        return ((end_price - start_price) / start_price) * 100
    except Exception:
        return None

period_moves = []
for a in analyzed:
    hist = stocks_data[a["name"]]["hist"]
    change = pct_change_over(hist, duration_days)
    if change is not None:
        period_moves.append({"name": a["name"], "symbol": a["symbol"], "price": a["ind"]["last_close"], "change": change})
df_moves = pd.DataFrame(period_moves)

col_up, col_down = st.columns(2)
if df_moves.empty:
    st.info(f"⚠️ لا توجد بيانات كافية بعد لمقارنة مدة \"{duration_choice}\" لأي سهم. جرب مدة أقصر.")
else:
    with col_up:
        st.markdown(f"**🔥 الأكثر ارتفاعاً ({duration_choice})**")
        for _, item in df_moves.sort_values(by="change", ascending=False).head(5).iterrows():
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="stock-title">{item['name']}</span>
                    <span class="price-up">+{item['change']:.2f}%</span>
                </div>
                <div style="font-size:0.85rem; color:#64748b; margin-top:4px;">{item['price']:.2f} EGP ({item['symbol']})</div>
            </div>
            """, unsafe_allow_html=True)
    with col_down:
        st.markdown(f"**🔻 الأكثر انخفاضاً ({duration_choice})**")
        for _, item in df_moves.sort_values(by="change", ascending=True).head(5).iterrows():
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="stock-title">{item['name']}</span>
                    <span class="price-down">{item['change']:.2f}%</span>
                </div>
                <div style="font-size:0.85rem; color:#64748b; margin-top:4px;">{item['price']:.2f} EGP ({item['symbol']})</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# 2. أفضل الفرص - مرتبة حسب النقاط الفنية الحقيقية
st.subheader("🌟 أفضل الفرص الاستثمارية (تحليل فني كمي)")

col_slider, col_filter = st.columns([2, 2])
with col_slider:
    score_threshold = st.slider(
        "صرامة الفلتر (عدد النقاط المطلوبة) — كل ما زاد، قلّت الإشارات لكن زادت جودتها عادةً",
        min_value=3, max_value=8, value=4, step=1
    )
with col_filter:
    timeframe_filter = st.selectbox(
        "فلتر حسب المدى الزمني للفرصة:",
        ["جميع المدى الزمني", "مضاربة يومية", "صعود أسبوعي", "صعود شهري (استثماري قصير)"],
        label_visibility="collapsed"
    )

with st.spinner("جاري قياس أداء هذه العتبة على بيانات تاريخية حقيقية (آخر سنة)..."):
    bt = run_full_backtest(stocks_data, score_threshold, strategy="momentum")

if bt["total"] >= 15:
    wr_color = "#16a34a" if bt["win_rate"] >= 55 else ("#d97706" if bt["win_rate"] >= 45 else "#dc2626")
    bh_line = f" | متوسط عائد الشراء والاحتفاظ لنفس الفترة: {bt['avg_buy_hold']:.1f}%." if bt["avg_buy_hold"] is not None else ""
    pf_text = f"{bt['profit_factor']:.2f}" if bt["profit_factor"] is not None else "—"
    aw_text = f"{bt['avg_win_pct']:+.1f}%" if bt["avg_win_pct"] is not None else "—"
    al_text = f"{bt['avg_loss_pct']:+.1f}%" if bt["avg_loss_pct"] is not None else "—"
    st.markdown(f"""
    <div class="data-note" style="border-right-color:{wr_color}; background-color:#f8fafc;">
    📊 <strong>نسبة النجاح التاريخية (آخر سنة):</strong>
    <span style="color:{wr_color}; font-weight:bold;">{bt['win_rate']:.0f}%</span>
    ({bt['wins']} ربح / {bt['losses']} خسارة من أصل {bt['total']} إشارة).{bh_line}<br>
    ⚖️ <strong>Profit Factor:</strong> {pf_text} (فوق 1.5 يعتبر جيد، فوق 2 ممتاز) |
    <strong>متوسط الربح:</strong> {aw_text} | <strong>متوسط الخسارة:</strong> {al_text}<br>
    هذا قياس فعلي على بيانات ماضية وليس ضماناً للمستقبل.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="data-note">
    ⚠️ عدد الإشارات التاريخية لهذه العتبة قليل جداً ({bt['total']}) خلال آخر سنة — العينة غير كافية لقياس موثوق. جرّب عتبة أقل.
    </div>
    """, unsafe_allow_html=True)

candidates = [a for a in analyzed_for_opps if a["score"] >= score_threshold]
if timeframe_filter != "جميع المدى الزمني":
    candidates = [a for a in candidates if a["timeframe"] == timeframe_filter]

# فلتر السيولة - استبعاد الأسهم ضعيفة التداول (تجنب فروقات سعرية واسعة وسهولة التلاعب)
min_liquidity = st.slider(
    "💧 الحد الأدنى لمتوسط قيمة التداول اليومي (EGP) - يستبعد الأسهم ضعيفة السيولة",
    min_value=0, max_value=1000000, value=100000, step=50000
)
before_liquidity = len(candidates)
candidates = [a for a in candidates if a["ind"]["avg_daily_value"] >= min_liquidity]
if before_liquidity > len(candidates):
    st.caption(f"💧 تم استبعاد {before_liquidity - len(candidates)} سهم بسيولة أقل من الحد المحدد.")

candidates.sort(key=lambda x: x["total_score"], reverse=True)

# تنويع قطاعي - بحد أقصى سهمين من نفس القطاع ضمن أفضل 8 فرص
diversified = []
sector_counts = {}
for a in candidates:
    sec = a["sector"]
    if sector_counts.get(sec, 0) >= 2:
        continue
    diversified.append(a)
    sector_counts[sec] = sector_counts.get(sec, 0) + 1
    if len(diversified) >= 8:
        break
candidates = diversified

with st.expander("🧮 حاسبة حجم الصفقة والمصاريف — اضبط بياناتك مرة واحدة"):
    col_cap, col_risk = st.columns(2)
    with col_cap:
        capital = st.number_input("رأس المال المتاح للتداول (EGP)", min_value=1000.0, value=50000.0, step=1000.0)
    with col_risk:
        risk_pct = st.slider("أقصى نسبة مخاطرة مقبولة لكل صفقة (%)", min_value=0.5, max_value=5.0, value=1.5, step=0.5)
    st.caption("القاعدة المتّبعة عند المحترفين: لا تخاطر بأكثر من 1-2% من رأس مالك في صفقة واحدة، بغض النظر عن مدى ثقتك في الفرصة.")

    st.markdown("**مصاريف التداول (تحقق من نسبتك الفعلية عند سمسارك في تلدا)**")
    col_comm, col_stamp = st.columns(2)
    with col_comm:
        commission_pct = st.number_input("عمولة السمسرة لكل عملية (%)", min_value=0.0, max_value=2.0, value=0.20, step=0.05)
    with col_stamp:
        stamp_pct = st.number_input("رسم الدمغة لكل عملية (%)", min_value=0.0, max_value=1.0, value=0.05, step=0.01)
    round_trip_cost_pct = 2 * (commission_pct + stamp_pct)  # مرة عند الشراء ومرة عند البيع
    st.caption(f"إجمالي تكلفة الدخول والخروج معاً: {round_trip_cost_pct:.2f}% من قيمة الصفقة — سيتم خصمها من هدف كل فرصة تلقائياً.")

if not candidates:
    st.info(f"لا توجد حالياً أسهم تحقق شروط فرصة قوية (نقاط ≥ {score_threshold}) ضمن هذا الفلتر. جرّب خفض الصرامة أو فلتر آخر.")
else:
    with st.spinner("جاري توليد الشرح الفني بالذكاء الاصطناعي..."):
        explanations = generate_ai_explanation(candidates)

    for c in candidates:
        ind = c["ind"]
        entry = ind["last_close"]
        target = entry + (2 * ind["atr14"])
        stop = entry - (1 * ind["atr14"])
        risk_per_share = entry - stop

        max_risk_egp = capital * (risk_pct / 100)
        suggested_shares = int(max_risk_egp / risk_per_share) if risk_per_share > 0 else 0
        suggested_shares = min(suggested_shares, int(capital / entry)) if entry > 0 else 0
        position_value = suggested_shares * entry

        gross_target_pct = ((target - entry) / entry) * 100 if entry > 0 else 0
        net_target_pct = gross_target_pct - round_trip_cost_pct
        net_warning = "" if net_target_pct > gross_target_pct * 0.5 else " ⚠️ المصاريف بتاكل جزء كبير من هامش الربح المتوقع"

        if c["total_score"] >= 9:
            rec, badge_class, border_color = "شراء قوي", "badge-buy-strong", "#16a34a"
        else:
            rec, badge_class, border_color = "شراء", "badge-buy", "#2563eb"

        # AI Score موحّد من 1-10 لسهولة المقارنة بين الفرص (المرجع الأقصى التقريبي = 18 نقطة)
        ai_score_10 = round(min(c["total_score"] / 18 * 10, 10), 1)

        reason = explanations.get(c["name"], " | ".join(c["tags"]))
        fund_line = " | ".join(c["fund_tags"]) if c["fund_tags"] else "بيانات أساسية غير متوفرة لهذا السهم على Yahoo Finance"
        alpha_line = f'<div style="font-size: 0.85rem; color: #7c3aed; margin-top:4px;"><strong>⚡ قوة نسبية:</strong> {c["alpha_tag"]}</div>' if c.get("alpha_tag") else ""

        st.markdown(f"""
        <div class="opp-card" style="border-right-color: {border_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 6px;">
                <span style="font-size: 1.15rem; font-weight: bold; color: #0f172a;">🎯 {c['name']}</span>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span class="badge-score" style="font-size:0.9rem;">🤖 AI Score: {ai_score_10}/10</span>
                    <span class="badge-time">⏱️ {c['timeframe']}</span>
                    <span class="{badge_class}">{rec}</span>
                </div>
            </div>
            <div style="text-align:center; font-size:0.75rem; color:#94a3b8; margin-bottom:8px;">
                (تفصيل: فني {c['score']} + أساسي {c['fund_score']}{' + قوة نسبية 1' if c.get('alpha_tag') else ''})
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; background-color: #f8fafc; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
                <div>
                    <div style="font-size: 0.75rem; color: #64748b;">السعر الحالي</div>
                    <div style="font-weight: bold; color: #0f172a;">{entry:.2f} EGP <span style="font-size:0.8rem;color:{'#16a34a' if ind['day_change_pct']>=0 else '#dc2626'};">({ind['day_change_pct']:+.2f}%)</span></div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #64748b;">سعر الدخول</div>
                    <div style="font-weight: bold; color: #0f172a;">{entry:.2f} EGP</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #64748b;">الهدف (2×ATR)</div>
                    <div style="font-weight: bold; color: #16a34a;">{target:.2f} EGP</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #64748b;">وقف الخسارة (1×ATR)</div>
                    <div style="font-weight: bold; color: #dc2626;">{stop:.2f} EGP</div>
                </div>
            </div>
            <div style="background-color: #eff6ff; padding: 8px 12px; border-radius: 8px; margin-bottom: 10px; font-size: 0.85rem; color: #1e3a8a;">
                📐 <strong>حجم الصفقة المقترح:</strong> {suggested_shares} سهم (~{position_value:,.0f} EGP) بناءً على مخاطرة {risk_pct}% من رأس مالك<br>
                💰 <strong>هامش الربح عند الهدف:</strong> {gross_target_pct:.1f}% قبل المصاريف → <strong>{net_target_pct:.1f}%</strong> بعد خصم {round_trip_cost_pct:.2f}% مصاريف{net_warning}
            </div>
            <div style="font-size: 0.9rem; color: #334155; margin-bottom: 6px;">
                <strong>💡 التحليل الفني:</strong> {reason}
            </div>
            <div style="font-size: 0.85rem; color: #475569;">
                <strong>📊 التحليل الأساسي:</strong> {fund_line}
            </div>
            {alpha_line}
        </div>
        """, unsafe_allow_html=True)

        # رسم بياني: آخر 60 يوم تداول مع المتوسطات المتحركة (بيانات حقيقية من نفس المصدر)
        try:
            full_close = stocks_data[c["name"]]["hist"]["Close"]
            chart_df = pd.DataFrame({
                "السعر": full_close,
                "SMA20": full_close.rolling(20).mean(),
                "SMA50": full_close.rolling(50).mean(),
            }).tail(60)
            st.line_chart(chart_df, height=180)
        except Exception:
            pass

    # تسجيل التوصيات الحالية في السجل تلقائياً مع سبب الدخول
    append_to_log(candidates, reasons=explanations)

st.markdown("---")

# 2.5 فرص ارتداد محتملة - استراتيجية مختلفة تماماً (Mean Reversion) - مخاطرة أعلى
st.subheader("🔄 فرص ارتداد محتملة (أسهم منخفضة - مخاطرة أعلى)")
st.markdown("""
<div class="disclaimer">
⚠️ <strong>هذه فئة مختلفة جذرياً عن "أفضل الفرص" أعلاه.</strong> هناك نبحث عن أسهم صاعدة بالفعل (زخم).
هنا نبحث عمداً عن أسهم <strong>منخفضة</strong> بدأت تُظهر بوادر ارتداد مبكرة (تشبع بيعي + زخم إيجابي حديث).
المخاطرة أعلى بكثير لأن الانخفاض قد يستمر ولا يوجد ضمان لارتداد فعلي (خطر "السكين الساقطة").
لا يُنصح بتخصيص أكثر من جزء صغير جداً من رأس المال لهذه الفئة، ولا تُسجَّل هذه الفرص في سجل الأداء الرئيسي لأنها استراتيجية مختلفة.
</div>
""", unsafe_allow_html=True)

reversal_threshold = st.slider("صرامة فلتر الارتداد", min_value=3, max_value=7, value=4, step=1, key="reversal_slider")

with st.spinner("جاري قياس أداء استراتيجية الارتداد على بيانات تاريخية حقيقية..."):
    bt_rev = run_full_backtest(stocks_data, reversal_threshold, strategy="reversal")

if bt_rev["total"] >= 15:
    wr_color_rev = "#16a34a" if bt_rev["win_rate"] >= 55 else ("#d97706" if bt_rev["win_rate"] >= 45 else "#dc2626")
    pf_text_rev = f"{bt_rev['profit_factor']:.2f}" if bt_rev["profit_factor"] is not None else "—"
    st.markdown(f"""
    <div class="data-note" style="border-right-color:{wr_color_rev};">
    📊 نسبة نجاح استراتيجية الارتداد تاريخياً (آخر سنة): <strong style="color:{wr_color_rev};">{bt_rev['win_rate']:.0f}%</strong>
    ({bt_rev['wins']} ربح / {bt_rev['losses']} خسارة من أصل {bt_rev['total']} إشارة) | Profit Factor: {pf_text_rev}
    </div>
    """, unsafe_allow_html=True)
else:
    st.caption(f"⚠️ عدد إشارات الارتداد التاريخية قليل ({bt_rev['total']}) — العينة غير كافية لقياس موثوق.")

# ⚖️ مقارنة سريعة بين الاستراتيجيتين على نفس البيانات التاريخية
if bt["total"] >= 5 or bt_rev["total"] >= 5:
    st.markdown("##### ⚖️ مقارنة سريعة بين الاستراتيجيتين (آخر سنة من البيانات الحقيقية)")
    comp_c1, comp_c2 = st.columns(2)
    with comp_c1:
        st.metric("نسبة نجاح الزخم", f"{bt['win_rate']:.0f}%" if bt["win_rate"] is not None else "—")
        st.caption(f"Profit Factor: {bt['profit_factor']:.2f} | عدد الإشارات: {bt['total']}" if bt["profit_factor"] is not None else f"عدد الإشارات: {bt['total']}")
    with comp_c2:
        st.metric("نسبة نجاح الارتداد", f"{bt_rev['win_rate']:.0f}%" if bt_rev["win_rate"] is not None else "—")
        st.caption(f"Profit Factor: {bt_rev['profit_factor']:.2f} | عدد الإشارات: {bt_rev['total']}" if bt_rev["profit_factor"] is not None else f"عدد الإشارات: {bt_rev['total']}")
    comp_df = pd.DataFrame({
        "نسبة النجاح %": [bt["win_rate"] or 0, bt_rev["win_rate"] or 0],
    }, index=["الزخم", "الارتداد"])
    st.bar_chart(comp_df)
    st.caption("⚠️ المقارنة على عتبات النقاط المختارة فوق حالياً لكل استراتيجية، وعلى بيانات ماضية فقط — مش ضماناً لأداء مستقبلي.")

reversal_candidates = [a for a in analyzed_for_opps if a["reversal_score"] >= reversal_threshold and a["ind"]["avg_daily_value"] >= min_liquidity]
reversal_candidates.sort(key=lambda x: x["reversal_score"], reverse=True)
reversal_candidates = reversal_candidates[:5]

if not reversal_candidates:
    st.info("لا توجد حالياً أسهم تحقق شروط ارتداد محتمل ضمن هذه العتبة.")
else:
    rev_payload = [{"name": a["name"], "ind": a["ind"], "score": a["reversal_score"], "tags": a["reversal_tags"], "timeframe": "ارتداد محتمل"} for a in reversal_candidates]
    with st.spinner("جاري توليد شرح فرص الارتداد بالذكاء الاصطناعي..."):
        rev_explanations = generate_ai_explanation(rev_payload)

    for a in reversal_candidates:
        ind = a["ind"]
        entry = ind["last_close"]
        target = entry + (1.5 * ind["atr14"])
        stop = entry - (0.8 * ind["atr14"])
        reason = rev_explanations.get(a["name"], " | ".join(a["reversal_tags"]))
        st.markdown(f"""
        <div class="opp-card" style="border-right-color: #d97706;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 6px;">
                <span style="font-size: 1.1rem; font-weight: bold; color: #0f172a;">🔻 {a['name']}</span>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span class="badge-score">⭐ {a['reversal_score']} نقطة ارتداد</span>
                    <span class="badge-watch">مخاطرة أعلى</span>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; background-color: #fffbeb; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
                <div><div style="font-size: 0.75rem; color: #64748b;">السعر الحالي</div><div style="font-weight: bold;">{entry:.2f} EGP</div></div>
                <div><div style="font-size: 0.75rem; color: #64748b;">هدف (مبدئي)</div><div style="font-weight: bold; color: #16a34a;">{target:.2f} EGP</div></div>
                <div><div style="font-size: 0.75rem; color: #64748b;">وقف خسارة (ضيق)</div><div style="font-weight: bold; color: #dc2626;">{stop:.2f} EGP</div></div>
            </div>
            <div style="font-size: 0.88rem; color: #334155;"><strong>💡 التحليل:</strong> {reason}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# 2.7 أفضل الأسهم من حيث الجودة الأساسية - بغض النظر عن حركة السعر (للمستثمر متوسط/طويل المدى)
st.subheader("🏆 أفضل الأسهم أساسياً (Quality) - بصرف النظر عن حركة السعر الحالية")
st.caption("هذه القائمة لا تنظر للزخم أو الاتجاه إطلاقاً، فقط لصحة الشركة المالية (P/E، العائد على حقوق الملكية، الدين، هامش الربح). مناسبة أكثر للاستثمار متوسط/طويل المدى وليس المضاربة السريعة.")

quality_candidates = [a for a in analyzed_for_opps if a["fund"]["available"] and a["fund_score"] >= 3]
quality_candidates.sort(key=lambda x: x["fund_score"], reverse=True)
quality_candidates = quality_candidates[:5]

if not quality_candidates:
    st.info("لا توجد حالياً أسهم ببيانات أساسية كافية تحقق معايير جودة عالية (نقاط أساسية ≥ 3).")
else:
    for a in quality_candidates:
        fund_line = " | ".join(a["fund_tags"])
        st.markdown(f"""
        <div class="stock-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="stock-title">{a['name']}</span>
                <span class="badge-score">⭐ {a['fund_score']}/5 جودة أساسية</span>
            </div>
            <div style="font-size:0.85rem; color:#475569; margin-top:6px;">{fund_line}</div>
            <div style="font-size:0.8rem; color:#64748b; margin-top:4px;">السعر الحالي: {a['ind']['last_close']:.2f} EGP</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# 3. سجل التوصيات وتتبع الأداء الفعلي
st.subheader("📒 سجل التوصيات وتتبع الأداء")

if not USE_GSHEETS:
    st.caption("💾 التخزين حالياً محلي مؤقت (هيتمسح عند أي تحديث للكود). راجع تعليمات ربط Google Sheets في آخر الصفحة عشان السجل يفضل محفوظ دائماً.")

log_df_raw = load_log()
if log_df_raw.empty:
    st.info("لا توجد توصيات مسجلة بعد. كل مرة تظهر فيها فرصة سيتم تسجيلها هنا تلقائياً بتاريخها، وتقدر تتابع نتيجتها لاحقاً.")
else:
    retention_days = st.slider(
        "🗓️ الاحتفاظ بالتوصيات لمدة (أيام) — الأقدم من كده بيتوقف عرضها تلقائياً",
        min_value=30, max_value=365, value=180, step=30,
        help="التوصيات مش محتاجة تتخزن للأبد. اضبط المدة حسب أفق استثمارك (شهر لحد سنة)."
    )
    hidden_count = len(log_df_raw) - len(purge_old_entries(log_df_raw, retention_days))
    if hidden_count > 0:
        cclean1, cclean2 = st.columns([3, 1])
        with cclean1:
            st.caption(f"🕓 تم إخفاء {hidden_count} توصية أقدم من {retention_days} يوم من العرض تحت (لسه موجودة في التخزين).")
        with cclean2:
            if st.button("🧹 حذفها نهائياً من السجل"):
                cleaned = purge_old_entries(log_df_raw, retention_days)
                if write_full_log(cleaned):
                    st.success(f"✅ اتحذفت {hidden_count} توصية قديمة نهائياً.")
                    st.rerun()
    log_df = purge_old_entries(log_df_raw, retention_days)

    col_hold, col_cap2 = st.columns(2)
    with col_hold:
        holding_days = st.slider(
            "⏱️ المدة الزمنية لتقييم كل توصية (أيام)", min_value=5, max_value=30, value=15, step=1,
            help="لو التوصية معدّتش الهدف ولا وقف الخسارة خلال المدة دي، هيتم تقييمها بسعر إغلاقها الفعلي في تاريخ الاستحقاق واعتبارها 'انتهت المهلة'."
        )
    with col_cap2:
        capital_per_trade = st.number_input(
            "💰 مبلغ افتراضي لكل توصية لحساب الربح/الخسارة (EGP)", min_value=1000.0, value=10000.0, step=1000.0,
            help="مبلغ نظري ثابت بيتفرض استثماره في كل توصية، عشان نحسب لو كنت نفذت التوصيات كنت هتكسب أو تخسر قد إيه."
        )

    current_prices = {a["name"]: a["ind"]["last_close"] for a in analyzed}
    evaluated = evaluate_log(log_df, current_prices, stocks_data, holding_days=holding_days, capital_per_trade=capital_per_trade)
    evaluated_sorted = evaluated.sort_values(by="التاريخ", ascending=False).reset_index(drop=True)
    pnl_col = f"الربح/الخسارة لو استثمرت {capital_per_trade:,.0f} جنيه"
    is_expired = evaluated_sorted["الحالة الحالية"].str.startswith("⏰ انتهت المهلة")

    # تنبيهات خروج فورية - أهم حاجة عملياً غير الإشارات نفسها
    hits = evaluated_sorted[evaluated_sorted["الحالة الحالية"] == "✅ تحقق الهدف"]
    stops = evaluated_sorted[evaluated_sorted["الحالة الحالية"] == "❌ ضرب وقف الخسارة"]
    expired = evaluated_sorted[is_expired]
    for _, row in hits.iterrows():
        st.success(f"🔔 {row['السهم']} وصل هدفه ({row['الهدف']} EGP) — فكّر تقفل الصفقة.")
    for _, row in stops.iterrows():
        st.warning(f"🔔 {row['السهم']} ضرب وقف الخسارة ({row['وقف الخسارة']} EGP) — الالتزام بالخروج أهم من التمني بالارتداد.")
    for _, row in expired.iterrows():
        emoji = "🟢" if (row["نسبة العائد %"] or 0) >= 0 else "🔴"
        precision_note = "" if "سعر تاريخي فعلي" in row["الحالة الحالية"] else " (تقدير تقريبي)"
        st.info(f"{emoji} {row['السهم']} عدّى {holding_days} يوم من غير ما يحقق هدف أو وقف — عائدها {row['نسبة العائد %']:+.1f}%{precision_note}.")

    # تنبيهات تليجرام - تُبعت مرة واحدة بس لكل توصية (بيتحدد عن طريق عمود "تم التنبيه؟" في السجل)
    if USE_TELEGRAM:
        to_notify = pd.concat([hits, stops])
        to_notify = to_notify[to_notify[NOTIFIED_COL] == False] if not to_notify.empty else to_notify
        if not to_notify.empty:
            sent_any = False
            for _, row in to_notify.iterrows():
                is_hit = row["الحالة الحالية"] == "✅ تحقق الهدف"
                emoji = "✅" if is_hit else "❌"
                level_word = "الهدف" if is_hit else "وقف الخسارة"
                level_val = row["الهدف"] if is_hit else row["وقف الخسارة"]
                msg = f"{emoji} {row['السهم']}: {row['الحالة الحالية']} عند {level_val} EGP ({level_word})"
                if send_telegram_message(msg):
                    sent_any = True
            if sent_any:
                raw_log_for_notify = load_log()
                notified_keys = set(zip(to_notify["التاريخ"], to_notify["السهم"]))
                raw_log_for_notify[NOTIFIED_COL] = raw_log_for_notify.apply(
                    lambda r: True if (r["التاريخ"], r["السهم"]) in notified_keys else r[NOTIFIED_COL], axis=1
                )
                write_full_log(raw_log_for_notify)

    open_count = (evaluated_sorted["الحالة الحالية"] == "⏳ لسه مفتوحة").sum()
    if open_count >= 5:
        st.info(f"📌 عندك {open_count} صفقة مفتوحة في السجل حالياً — فكّر تقفل بعضها قبل ما تدخل فرص جديدة، عشان متركزش مخاطرة كبيرة في نفس الوقت.")

    # نسبة النجاح: مقياس دقة التوصيات نفسها (بغض النظر هل نفّذتها أنت فعلاً ولا لأ)
    wins_count = len(hits) + (expired["نسبة العائد %"] >= 0).sum()
    losses_count = len(stops) + (expired["نسبة العائد %"] < 0).sum()
    closed = wins_count + losses_count
    if closed > 0:
        actual_wr = (wins_count / closed) * 100
        st.markdown(f"""
        <div class="data-note">
        📈 <strong>نسبة نجاح التوصيات نفسها (دقة النظام):</strong> {actual_wr:.0f}% ({wins_count} ربح / {losses_count} خسارة من أصل {closed} توصية مغلقة أو منتهية المهلة).
        هذا رقم عن دقة التوصية ذاتها بصرف النظر هل نفذتها فعلاً ولا لأ.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### ✅ حدد التوصيات اللي نفّذتها فعلاً بفلوسك")
    st.caption("علّم فقط على اللي دخلت فيها فعلياً — عشان ملخص الربح/الخسارة تحت يبقى معبّر عن أداءك الحقيقي، مش أداء افتراضي لكل التوصيات.")

    display_cols = ["التاريخ", "السهم", "الرمز", "سعر الدخول", "الهدف", "وقف الخسارة",
                     "الحالة الحالية", "أيام مرت", "نسبة العائد %", pnl_col, "سبب الدخول", EXEC_COL]
    edited_df = st.data_editor(
        evaluated_sorted[display_cols],
        use_container_width=True,
        hide_index=True,
        disabled=[c for c in display_cols if c != EXEC_COL],
        column_config={
            EXEC_COL: st.column_config.CheckboxColumn(EXEC_COL, help="حدد التوصيات اللي دخلت فيها فعلياً بفلوسك")
        },
        key="log_editor"
    )

    save_col, _ = st.columns([1, 3])
    with save_col:
        if st.button("💾 حفظ تحديد التوصيات المنفذة"):
            raw_log = load_log()  # نستخدم السجل الكامل (غير المصفّى) عشان متفقدش صفوف قديمة عند الحفظ
            merged = raw_log.merge(
                edited_df[["التاريخ", "السهم", EXEC_COL]],
                on=["التاريخ", "السهم"], how="left", suffixes=("", "_جديد")
            )
            merged[EXEC_COL] = merged[EXEC_COL + "_جديد"].combine_first(merged[EXEC_COL])
            merged = merged.drop(columns=[EXEC_COL + "_جديد"])
            if write_full_log(merged):
                st.success("✅ اتحفظ. حدّث الصفحة تشوف الملخص متغيّر لو غيّرت الفلتر تحت.")

    # --- ملخص الربح/الخسارة الفعلي لو تم تنفيذ التوصيات ---
    st.markdown("---")
    perf_basis = st.radio(
        "💵 احسب ملخص الربح/الخسارة على أساس:",
        ["كل التوصيات المسجلة (افتراضي)", "بس اللي حدّدتها فوق كـ منفذة فعلاً"],
        horizontal=True
    )
    base_df = evaluated_sorted
    if not perf_basis.startswith("كل"):
        exec_keys = edited_df.loc[edited_df[EXEC_COL] == True, ["التاريخ", "السهم"]]
        base_df = evaluated_sorted.merge(exec_keys, on=["التاريخ", "السهم"], how="inner")

    closed_mask = base_df["الحالة الحالية"].isin(["✅ تحقق الهدف", "❌ ضرب وقف الخسارة"]) | base_df["الحالة الحالية"].str.startswith("⏰ انتهت المهلة")
    closed_df = base_df[closed_mask].dropna(subset=[pnl_col])

    if not closed_df.empty:
        total_pnl = closed_df[pnl_col].sum()
        avg_return = closed_df["نسبة العائد %"].mean()
        best = closed_df.loc[closed_df["نسبة العائد %"].idxmax()]
        worst = closed_df.loc[closed_df["نسبة العائد %"].idxmin()]

        st.markdown("##### 💵 ملخص الربح/الخسارة")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("صافي الربح/الخسارة", f"{total_pnl:,.0f} EGP")
        c2.metric("متوسط العائد لكل توصية", f"{avg_return:+.1f}%")
        c3.metric("🏆 أفضل توصية", f"{best['السهم']}", f"{best['نسبة العائد %']:+.1f}%")
        c4.metric("📉 أسوأ توصية", f"{worst['السهم']}", f"{worst['نسبة العائد %']:+.1f}%")
        st.caption(
            f"⚠️ حساب افتراضي بفرض استثمار {capital_per_trade:,.0f} جنيه في كل توصية، من غير خصم مصاريف السمسرة والدمغة، "
            f"وبناءً على {len(closed_df)} توصية مغلقة أو منتهية المهلة ({perf_basis}). التوصيات المفتوحة لسه مش داخلة في الحساب ده."
        )

        open_df = base_df[base_df["الحالة الحالية"] == "⏳ لسه مفتوحة"].dropna(subset=[pnl_col])
        if not open_df.empty:
            unrealized_pnl = open_df[pnl_col].sum()
            st.caption(f"📌 لو قفلت الـ {len(open_df)} توصية المفتوحة حالياً بالسعر الحالي (غير محقق)، كان ممكن يزيد/ينقص صافي ربحك بـ {unrealized_pnl:,.0f} EGP تقريبًا.")
    else:
        st.caption("لسه مفيش توصيات مغلقة أو انتهت مهلتها ضمن الأساس المختار عشان نحسب الربح/الخسارة الفعلي.")

    csv_data = evaluated_sorted.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ تحميل السجل كامل (CSV)", data=csv_data, file_name="سجل_التوصيات.csv", mime="text/csv")

    if USE_GSHEETS:
        st.caption("✅ السجل متصل بـ Google Sheets — هيفضل محفوظ حتى بعد أي تحديث للتطبيق (حسب مدة الاحتفاظ اللي حددتها فوق).")
    else:
        st.caption("⚠️ ملاحظة: السجل حالياً مخزّن مؤقتاً على خادم التطبيق وهيتمسح عند أي تحديث للكود. حمّل نسخة CSV بشكل دوري، أو اربط Google Sheets (تعليمات في آخر الصفحة) عشان يفضل محفوظ دائماً.")

_data_date_str = data_as_of_date.strftime('%Y-%m-%d') if data_as_of_date else "غير معروف"
st.caption(f"تاريخ آخر بيانات فعلية: {_data_date_str} | وقت فتحك للتطبيق: {datetime.now().strftime('%Y-%m-%d %H:%M')} | المصدر: Yahoo Finance (بيانات حقيقية، تأخير طبيعي محتمل خصوصاً للبورصة المصرية)")

if not USE_GSHEETS:
    with st.expander("🔧 عايز السجل يفضل محفوظ دائماً؟ اضغط هنا (إعداد لمرة واحدة، 10 دقائق)"):
        st.markdown("""
حالياً السجل بيتخزن مؤقتاً على خادم Streamlit، وبيتمسح كل مرة تعمل فيها تحديث للكود. عشان تحله نهائياً، اربط
التطبيق بـ Google Sheet مجاني — خطوات لمرة واحدة فقط:

**1) اعمل Google Sheet جديد**
- افتح [sheets.google.com](https://sheets.google.com) واعمل شيت جديد فاضي، وسمّيه أي اسم (مثلاً "سجل التوصيات").
- خد رابط الشيت من شريط العنوان (URL) وخليه جاهز.

**2) اعمل حساب خدمة (Service Account) من Google Cloud (مجاني)**
- روح [console.cloud.google.com](https://console.cloud.google.com) وسجّل دخول بنفس حساب Google.
- اعمل مشروع جديد (New Project) بأي اسم.
- من قائمة البحث فوق، دوّر على **Google Sheets API** وفعّلها (Enable) للمشروع.
- من القائمة الجانبية: **APIs & Services → Credentials → Create Credentials → Service Account**.
- اديله أي اسم واضغط Done.
- افتح الـ Service Account اللي عملته، روح تبويب **Keys → Add Key → Create new key → JSON**، وهينزلّك ملف JSON. خليه في مكان آمن.

**3) شارك الشيت مع حساب الخدمة**
- افتح ملف الـ JSON، هتلاقي فيه سطر زي `"client_email": "xxxx@xxxx.iam.gserviceaccount.com"`.
- ارجع للـ Google Sheet اللي عملته، اضغط **Share**، وحط الإيميل ده كـ **Editor**.

**4) ضيف البيانات في إعدادات (Secrets) Streamlit**
- من لوحة تحكم Streamlit Cloud، افتح تطبيقك → **Settings → Secrets**، والصق الآتي (استبدل القيم من ملف الـ JSON):
```
GSHEET_URL = "رابط الشيت اللي نسخته في خطوة 1"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```
كل القيم دي موجودة جاهزة جوه ملف الـ JSON، بس انسخها زي ما هي (خصوصاً `private_key` خليه بين علامتي تنصيص).

**5) ضيف المكتبات المطلوبة**
- في ملف `requirements.txt` بتاع مشروعك، ضيف سطرين:
```
gspread
google-auth
requests
```

**6) اعمل Reboot للتطبيق**
- بعد حفظ الـ Secrets، اعمل Reboot للتطبيق من Streamlit Cloud. لو الإعداد صح، هتلاقي في آخر السجل رسالة "✅ السجل متصل بـ Google Sheets" بدل التنبيه الحالي.

⚠️ لو مش عايز تعمل الخطوات دي دلوقتي، مفيش مشكلة — التطبيق شغال عادي بالتخزين المؤقت، وبس خد بالك تحمّل نسخة CSV بزرار التحميل فوق قبل أي تحديث للكود عشان متفقدش السجل.
        """)

if not USE_TELEGRAM:
    with st.expander("🔔 عايز تنبيه فوري لما توصية توصل هدفها أو تضرب وقف الخسارة؟ اضغط هنا (5 دقائق)"):
        st.markdown("""
تقدر تستقبل رسالة تليجرام فورية أول ما توصية في سجلك تحقق هدفها أو تضرب وقف الخسارة، بدل ما تفتح التطبيق كل يوم تتفقد بنفسك.

**1) اعمل بوت تليجرام**
- افتح تليجرام ودوّر على المستخدم **@BotFather**، ابعتله `/newbot` واتبع التعليمات (اسم للبوت واسم مستخدم ينتهي بـ bot).
- هيديك رمز (Token) شكله زي `123456789:AAExxxxxxxxxxxxxxxxxxxxxxx` — احفظه.

**2) اعرف رقم الـ Chat ID بتاعك**
- ابعت أي رسالة (مثلاً "hi") للبوت اللي عملته من حسابك في تليجرام.
- افتح الرابط ده في المتصفح بعد ما تحط رمز البوت مكان TOKEN:
  `https://api.telegram.org/botTOKEN/getUpdates`
- هتلاقي في الرد رقم `"id"` جوه `"chat"` — ده الـ Chat ID بتاعك.

**3) ضيفهم في إعدادات (Secrets) Streamlit**
- في نفس مكان الـ Secrets (Settings → Secrets)، ضيف السطرين دول:
```
TELEGRAM_BOT_TOKEN = "الرمز اللي أخدته من BotFather"
TELEGRAM_CHAT_ID = "الرقم اللي أخدته من getUpdates"
```

**4) اعمل Reboot للتطبيق**
بعدها هتوصلك رسالة تليجرام أول ما أي توصية توصل هدفها أو تضرب وقف الخسارة — مرة واحدة بس لكل توصية عشان متتكررش الرسائل.
        """)

