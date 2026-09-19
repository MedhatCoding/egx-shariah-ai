# -*- coding: utf-8 -*-
"""
تقرير تليجرام يومي شامل - نفس تحليلات تطبيق Streamlit بالضبط:
فني (اتجاه/زخم/RSI/سيولة/ADX/تأكيد أسبوعي) + أساسي (P/E/ROE/دين/هامش ربح) +
قوة نسبية مقابل EGX30 + فرص ارتداد + الأكثر ارتفاعاً وانخفاضاً + الذهب العالمي.
يسجل في Google Sheets ويتابع الأهداف/وقف الخسارة تلقائياً.
كل الإعدادات من متغيرات البيئة (GitHub Secrets) - لا يوجد أي Token داخل الكود.
"""

import os
import json
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime

# ============================================================
# 1) قائمة الأسهم الموحدة (113 سهم - نفس قائمة التطبيق بالضبط)
# ============================================================
SHARIAH_STOCKS = {
    "القاهرة للخدمات التعليمية": "CAED.CA", "شركة مستشفي كليوباترا": "CLHO.CA",
    "كوبر للاستثمار التجاري والتطوير العقاري": "COPR.CA", "القاهرة للزيوت والصابون": "COSG.CA",
    "شركة القاهرة للأدوية": "CPCI.CA", "كريستمارك للمقاولات والتطوير العمراني": "CRST.CA",
    "ديجتايز للاستثمار والتقنية": "DGTZ.CA", "العربية لاستصلاح الاراضي": "EALR.CA",
    "مطاحن شرق الدلتا": "EDFM.CA", "العامة لاستصلاح الاراضي و التنمية": "AALR.CA",
    "الشركة العربية لادارة وتطوير الاصول": "ACAMD.CA", "مصرف أبو ظبي الإسلامي - مصر": "ADIB.CA",
    "اراب للتنمية والاستثمار العقاري": "ADRI.CA", "مطاحن ومخابز الاسكندرية": "AFMC.CA",
    "اطلس للاستثمار والصناعات الغذائية": "AIFI.CA", "اجواء للصناعات الغذائية - مصر": "AJWA.CA",
    "الاسكندرية للخدمات الطبية - المركز الطبي": "AMES.CA", "الاسكندرية للزيوت المعدنية": "AMOC.CA",
    "نوفيدا للإستثمار والتكنولوجيا": "AMPI.CA", "ايديتا للصناعات الغذائية": "EFID.CA",
    "مصر للألومنيوم": "EGAL.CA", "غاز مصر": "EGAS.CA",
    "المصريين للاسكان والتنمية والتعمير": "EHDR.CA", "المصرية للمشروعات السياحية": "EITP.CA",
    "النصر لتصنيع الحاصلات الزراعية": "ELNA.CA", "بنك فيصل الاسلامي المصري - بالدولار": "FAITA.CA",
    "فيوتشر كير للصناعات الطبية": "FCMD.CA", "الاولي للاستثمار والتنمية العقارية": "FIRE.CA",
    "العبوات الدوائية المتطورة": "APPC.CA", "العربيه وبولفارا للغزل والنسيج - يونيراب": "APSW.CA",
    "العربية للاسمنت": "ARCC.CA", "التوفيق للتأجير التمويلي - أية.تي.ليس": "ATLC.CA",
    "مصر الوطنية للصلب - عتاقة": "ATQA.CA", "الاسكندرية للادوية والصناعات الكيماوية": "AXPH.CA",
    "بي اي دي- البدر للاستثمار والتنمية": "BIDI.CA", "بي اي جي للتجارة والاستثمار": "BIGP.CA",
    "جلاكسو سميث كلاين": "BIOC.CA", "الفنار للمقاولات العمومية والإنشاءات الهندسية": "FNAR.CA",
    "الغربية الإسلامية للتنمية العمرانية": "GIHD.CA", "مجموعة جي . أم . سي للاستثمارات الصناعية": "GMCI.CA",
    "جي بي آي للنمو العمراني": "GPIM.CA", "جلوبال تليكوم القابضة": "GTHE.CA",
    "الدولية للأسمدة والكيماويات": "ICFC.CA", "المشروعات الصناعية والهندسية": "IEEC.CA",
    "الدوليه للمحاصيل الزراعيه": "IFAP.CA", "المجموعة المتكاملة للأعمال الهندسية": "INEG.CA",
    "سماد مصر (ايجيفرت)": "SMFR.CA", "الاسكندرية للغزل والنسيج (سبينهوس)": "SPIN.CA",
    "سبيد ميديكال": "SPMD.CA", "تنمية للاستثمار العقاري": "TANM.CA",
    "مطاحن مصر العليا": "UEFM.CA", "الاتحاد الصيدلي للخدمات الطبية والاستثمار": "UPMS.CA",
    "فرتيكا للصناعة و التجارة": "VERT.CA", "وادي كوم امبو لاستصلاح الاراضي": "WKOL.CA",
    "الزيوت المستخلصة ومنتجاتها": "ZEOT.CA", "فوديكو - الاسماعيلية الوطنية للصناعات الغذائية": "INFI.CA",
    "الاسماعيلية مصر للدواجن": "ISMA.CA", "الحديد والصلب للمناجم والمحاجر": "ISMQ.CA",
    "جهينة للصناعات الغذائية": "JUFO.CA", "النصر للملابس والمنسوجات - كابو": "KABO.CA",
    "مصر بني سويف للاسمنت": "MBSC.CA", "مصر للاسمنت - قنا": "MCQE.CA",
    "ماكرو جروب": "MCRO.CA", "مصر لإنتاج الأسمدة - موبكو": "MFPC.CA",
    "مصر لصناعة الكيماويات": "MICH.CA", "مطاحن ومخابز شمال القاهرة": "MILS.CA",
    "مصر انتركونتنتال لصناعة الجرانيت والرخام": "MISR.CA", "المصرية الكويتية للاستثمار والتجارة": "MKIT.CA",
    "مرسى مرسى علم للتنمية السياحية": "MMAT.CA", "المصرية لنظم التعليم الحديثة": "MOED.CA",
    "مصر للزيوت والصابون": "MOSC.CA", "ممفيس للادوية والصناعات الكيماوية": "MPCI.CA",
    "المنصورة للدواجن": "MPCO.CA", "ام.ام جروب للصناعة والتجارة العالمية": "MTIE.CA",
    "النصر للاعمال المدنية": "NCCW.CA", "النيل لحليج الاقطان": "NCGC.CA",
    "شمال الصعيد للتنمية والانتاج الزراعي (نيوداب)": "NEDA.CA", "مستشفى النزهة الدولي": "NINH.CA",
    "شركة العبور للإستثمار العقاري": "OBRI.CA", "اكتوبر فارما": "OCPH.CA",
    "البويات والصناعات الكيماوية - باكين": "PACH.CA", "بريميم هيلثكير جروب": "PHGC.CA",
    "القاهرة للدواجن": "POUL.CA", "الشركة العامة لمنتجات السيراميك والبورسلين": "PRCL.CA",
    "الاستثمار العقاري العربي - اليكو": "RREI.CA", "رووبكس العالمية لتصنيع البلاستيك والاكريليك": "RUBX.CA",
    "بنك البركة مصر": "SAUD.CA", "اسمنت سيناء": "SCEM.CA",
    "مطاحن ومخابز جنوب القاهرة وگيزة": "SCFM.CA", "سبأ الدولية للأدوية والصناعات الكيماوية": "SIPC.CA",
    "سيدي كرير للبتروكيماويات": "SKPC.CA", "المصرية للاتصالات": "ETEL.CA",
    "السويدي إليكتريك": "SWDY.CA", "طلعت مصطفى القابضة": "TMGH.CA",
    "بالم هيلز للتعمير": "PHDC.CA", "سوديك": "OCDI.CA",
    "جي بي أوتو": "AUTO.CA", "فوري لتكنولوجيا البنوك والمدفوعات الإلكترونية": "FWRY.CA",
    "ابن سينا فارما": "ISPH.CA", "النساجون الشرقيون": "ORWE.CA",
    "مدينة نصر للإسكان والتعمير": "MNHD.CA", "أوراسكوم للإنشاءات": "ORAS.CA",
    "أوراسكوم للتنمية": "ORHD.CA", "إعمار مصر للتنمية": "EMFD.CA",
    "عبور لاند للصناعات الغذائية": "OLFI.CA", "أبو قير للأسمدة والصناعات الكيماوية": "ABUK.CA",
    "راية القابضة": "RAYA.CA", "راية لخدمات مراكز الاتصال": "RACC.CA",
    "تعليم لخدمات الإدارة": "TAMD.CA", "ايجيترانس (مصر لخدمات النقل)": "ETRS.CA",
    "العربية لحليج الأقطان": "ACGC.CA", "العز للسيراميك والبورسلين (الجوهرة)": "ECAP.CA",
    "بنك فيصل الإسلامي المصري - بالجنيه": "FAIT.CA",
}

SCORE_THRESHOLD = int(os.environ.get("SCORE_THRESHOLD", "4"))
REVERSAL_THRESHOLD = int(os.environ.get("REVERSAL_THRESHOLD", "4"))
MIN_LIQUIDITY = float(os.environ.get("MIN_LIQUIDITY", "100000"))
MAX_ALERTS = 8

LOG_COLUMNS = ["التاريخ", "السهم", "الرمز", "سعر الدخول", "الهدف", "وقف الخسارة", "النقاط", "سبب الدخول", "نُفّذت فعلاً؟", "سعر التنفيذ الفعلي", "تم التنبيه؟", "المصدر"]


# ============================================================
# 2) المؤشرات الفنية (نفس منطق التطبيق بالضبط)
# ============================================================
def compute_indicators(hist: pd.DataFrame):
    close, high, low, volume = hist["Close"], hist["High"], hist["Low"], hist["Volume"]
    last_close = float(close.iloc[-1])
    prev_close = float(close.iloc[-2])
    day_change_pct = ((last_close - prev_close) / prev_close) * 100
    sma20 = float(close.rolling(20).mean().iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else float(close.rolling(len(close)).mean().iloc[-1])

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    rsi14 = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else 50.0

    prev_close_series = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close_series).abs(), (low - prev_close_series).abs()], axis=1).max(axis=1)
    atr14 = float(tr.rolling(14).mean().iloc[-1])

    momentum_5d = ((last_close - float(close.iloc[-6])) / float(close.iloc[-6])) * 100 if len(close) > 6 else 0.0
    momentum_20d = ((last_close - float(close.iloc[-21])) / float(close.iloc[-21])) * 100 if len(close) > 21 else 0.0

    avg_vol20 = float(volume.rolling(20).mean().iloc[-1])
    last_vol = float(volume.iloc[-1])
    vol_ratio = (last_vol / avg_vol20) if avg_vol20 > 0 else 1.0
    avg_daily_value = avg_vol20 * last_close

    high_52w, low_52w = float(high.max()), float(low.min())
    pct_from_high = ((last_close - high_52w) / high_52w) * 100

    weekly_confirmed = False
    try:
        weekly_close = close.resample("W").last().dropna()
        if len(weekly_close) >= 5:
            wma4 = weekly_close.rolling(4).mean().iloc[-1]
            weekly_confirmed = bool(weekly_close.iloc[-1] > wma4)
    except Exception:
        pass

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
        "last_close": last_close, "day_change_pct": day_change_pct, "sma20": sma20, "sma50": sma50,
        "rsi14": rsi14, "atr14": atr14, "adx14": adx14, "momentum_5d": momentum_5d, "momentum_20d": momentum_20d,
        "vol_ratio": vol_ratio, "high_52w": high_52w, "low_52w": low_52w, "pct_from_high": pct_from_high,
        "avg_daily_value": avg_daily_value, "weekly_confirmed": weekly_confirmed,
    }


def score_opportunity(ind):
    score, tags = 0, []
    if ind["last_close"] > ind["sma20"] > ind["sma50"]:
        score += 3; tags.append("اتجاه صاعد مؤكد")
    elif ind["last_close"] > ind["sma20"]:
        score += 1; tags.append("فوق المتوسط قصير المدى")
    if ind.get("day_change_pct", 0) < -10:
        score -= 3; tags.append(f"⚠️ انخفاض حاد اليوم ({ind['day_change_pct']:.1f}%) - احتمال خبر سلبي")
    if ind["momentum_5d"] > 4:
        score += 2; tags.append("زخم قوي 5 أيام")
    elif ind["momentum_5d"] > 1:
        score += 1
    if 50 <= ind["rsi14"] <= 68:
        score += 2; tags.append(f"RSI صحي ({ind['rsi14']:.0f})")
    elif ind["rsi14"] > 75:
        score -= 2; tags.append(f"تشبع شرائي ({ind['rsi14']:.0f}) - حذر")
    if ind["vol_ratio"] > 1.8:
        score += 2; tags.append(f"سيولة استثنائية ({ind['vol_ratio']:.1f}x)")
    elif ind["vol_ratio"] > 1.3:
        score += 1
    if ind["pct_from_high"] > -8:
        score += 1; tags.append("قريب من القمة")
    if ind.get("weekly_confirmed"):
        score += 1; tags.append("تأكيد أسبوعي")
    if ind.get("adx14", 0) >= 25:
        score += 1; tags.append(f"اتجاه قوي (ADX {ind['adx14']:.0f})")
    return score, tags


def score_reversal_opportunity(ind):
    # شرط إجباري: لازم تشبع بيعي فعلي (RSI<45) وإلا مش فرصة ارتداد مهما كانت باقي العوامل
    if ind["rsi14"] >= 45:
        return 0, []
    score, tags = 2 if ind["rsi14"] < 35 else 1, []
    tags.append(f"تشبع بيعي ({ind['rsi14']:.0f})")
    if ind["pct_from_high"] < -20:
        score += 1; tags.append(f"منخفض {abs(ind['pct_from_high']):.0f}% عن القمة")
    if ind["momentum_5d"] > 1:
        score += 2; tags.append("بوادر ارتداد - زخم إيجابي حديث")
    if ind["vol_ratio"] > 1.5:
        score += 1; tags.append(f"سيولة مرتفعة ({ind['vol_ratio']:.1f}x)")
    if ind["last_close"] > ind["sma20"]:
        score += 1; tags.append("عاد فوق المتوسط قصير المدى")
    return score, tags


# ============================================================
# 3) التحليل الأساسي (نفس منطق التطبيق)
# ============================================================
def fetch_fundamentals(symbol):
    try:
        info = yf.Ticker(symbol).info
        pe = info.get("trailingPE")
        roe = info.get("returnOnEquity")
        debt_to_equity = info.get("debtToEquity")
        profit_margin = info.get("profitMargins")
        market_price = info.get("regularMarketPrice") or info.get("currentPrice")
        available = any(v is not None for v in [pe, roe, debt_to_equity, profit_margin])
        return {"available": available, "pe": pe, "roe": roe, "debt_to_equity": debt_to_equity, "profit_margin": profit_margin, "market_price": market_price}
    except Exception:
        return {"available": False, "pe": None, "roe": None, "debt_to_equity": None, "profit_margin": None, "market_price": None}


def score_fundamentals(fund):
    if not fund["available"]:
        return 0, []
    score, tags = 0, []
    if fund["pe"] is not None and fund["pe"] > 0:
        if fund["pe"] < 12:
            score += 2; tags.append(f"تقييم رخيص (P/E {fund['pe']:.1f})")
        elif fund["pe"] < 20:
            score += 1
    if fund["roe"] is not None and fund["roe"] > 0.10:
        score += 1; tags.append(f"ROE جيد ({fund['roe']*100:.0f}%)")
    if fund["debt_to_equity"] is not None and fund["debt_to_equity"] < 100:
        score += 1; tags.append("مديونية منخفضة")
    if fund["profit_margin"] is not None and fund["profit_margin"] > 0.10:
        score += 1; tags.append(f"هامش ربح صحي ({fund['profit_margin']*100:.0f}%)")
    return score, tags


# ============================================================
# 4) اتجاه السوق العام (EGX30) - للقوة النسبية (Alpha)
# ============================================================
def fetch_market_trend():
    try:
        hist = yf.Ticker("^CASE30").history(period="6mo", interval="1d")
        if hist.empty or len(hist) < 55:
            return None
        ind = compute_indicators(hist)
        if ind["last_close"] > ind["sma20"] > ind["sma50"]:
            label = "📈 صاعد"
        elif ind["last_close"] < ind["sma20"] < ind["sma50"]:
            label = "📉 هابط"
        else:
            label = "↔️ متذبذب"
        return {"label": label, "ind": ind}
    except Exception:
        return None


# ============================================================
# 5) جلب بيانات الأسهم والذهب
# ============================================================
def fetch_all_data():
    results = {}
    for name, symbol in SHARIAH_STOCKS.items():
        try:
            hist = yf.Ticker(symbol).history(period="1y", interval="1d")
            if hist.empty or len(hist) < 60:
                continue
            # قفزة يومية شاذة (>60%) غالباً خطأ split أو بيانات تالفة - نستبعد السهم كاملاً
            if hist["Close"].pct_change().abs().max() > 0.6:
                continue
            results[name] = {"symbol": symbol.replace(".CA", ""), "hist": hist}
        except Exception:
            continue
    return results


def fetch_gold_view():
    try:
        hist = yf.Ticker("GC=F").history(period="1y", interval="1d")
        if hist.empty or len(hist) < 60:
            return None
        ind = compute_indicators(hist)
        tech_score, tech_tags = score_opportunity(ind)
        rev_score, rev_tags = score_reversal_opportunity(ind)
        return {"ind": ind, "tech_score": tech_score, "tech_tags": tech_tags, "rev_score": rev_score, "rev_tags": rev_tags}
    except Exception:
        return None


# ============================================================
# 6) تليجرام
# ============================================================
def send_telegram_message(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID غير موجودين.")
        return False
    import requests
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=15)
        if r.status_code != 200:
            print(f"⚠️ فشل إرسال تليجرام - كود {r.status_code}. الرد: {r.text}")
            return False
        return True
    except Exception as e:
        print("⚠️ فشل إرسال تليجرام (استثناء):", e)
        return False


def send_report_sections(sections):
    """يبعت كل قسم كرسالة منفصلة (تجنباً لتخطي حد 4096 حرف لكل رسالة في تليجرام)."""
    sent, failed = 0, 0
    for section in sections:
        if send_telegram_message(section):
            sent += 1
        else:
            failed += 1
    print(f"📨 تم إرسال {sent} قسم بنجاح، فشل {failed}.")


# ============================================================
# 7) Google Sheets
# ============================================================
def get_worksheet():
    gsheet_url = os.environ.get("GSHEET_URL")
    creds_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
    if not gsheet_url or not creds_json:
        return None
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        creds_dict = json.loads(creds_json)
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_url(gsheet_url)
        try:
            ws = sh.worksheet("log")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title="log", rows=2000, cols=len(LOG_COLUMNS) + 2)
            ws.append_row(LOG_COLUMNS)
        return ws
    except Exception as e:
        print("⚠️ تعذر الاتصال بـ Google Sheets:", e)
        return None


def append_new_candidates_to_log(ws, candidates, report_date):
    if ws is None or not candidates:
        return
    try:
        records = ws.get_all_records()
        existing = {(r.get("التاريخ"), r.get("السهم")) for r in records}
    except Exception as e:
        print("⚠️ تعذرت قراءة السجل الحالي:", e)
        existing = set()

    new_rows = []
    for c in candidates:
        if (report_date, c["name"]) in existing:
            continue
        ind = c["ind"]
        new_rows.append([
            report_date, c["name"], c["symbol"],
            round(ind["last_close"], 2),
            round(ind["last_close"] + 2 * ind["atr14"], 2),
            round(ind["last_close"] - 1 * ind["atr14"], 2),
            c["total_score"], " | ".join(c["tags"])[:200],
            False, "", False, "تليجرام تلقائي",
        ])
    if new_rows:
        try:
            ws.append_rows(new_rows, value_input_option="USER_ENTERED")
            print(f"✅ تم تسجيل {len(new_rows)} توصية جديدة في Google Sheets.")
        except Exception as e:
            print("⚠️ تعذر إضافة الصفوف الجديدة:", e)


def check_hits_and_stops(ws, current_prices: dict):
    if ws is None:
        return
    try:
        records = ws.get_all_records()
    except Exception as e:
        print("⚠️ تعذرت قراءة السجل لفحص الأهداف/الوقف:", e)
        return
    if not records:
        return

    rows_to_update = []
    for i, r in enumerate(records):
        already_notified = str(r.get("تم التنبيه؟", "")).strip().lower() in ("true", "1", "yes", "نعم")
        if already_notified:
            continue
        name = r.get("السهم")
        current = current_prices.get(name)
        if current is None:
            continue
        try:
            target = float(r.get("الهدف"))
            stop = float(r.get("وقف الخسارة"))
        except (ValueError, TypeError):
            continue
        if current >= target:
            rows_to_update.append((i + 2, f"✅ <b>{name}</b>: تحقق الهدف عند {target} EGP (الحالي {current:.2f})"))
        elif current <= stop:
            rows_to_update.append((i + 2, f"❌ <b>{name}</b>: ضرب وقف الخسارة عند {stop} EGP (الحالي {current:.2f})"))

    if not rows_to_update:
        return
    notified_col_index = LOG_COLUMNS.index("تم التنبيه؟") + 1
    sent_count = 0
    for row_num, msg in rows_to_update:
        if send_telegram_message(msg):
            sent_count += 1
            try:
                ws.update_cell(row_num, notified_col_index, True)
            except Exception as e:
                print("⚠️ تعذر تحديث عمود التنبيه:", e)
    print(f"🔔 تم إرسال {sent_count} من أصل {len(rows_to_update)} تنبيه هدف/وقف خسارة.")


# ============================================================
# 8) التشغيل الرئيسي
# ============================================================
def main():
    print(f"[{datetime.now()}] بدء المسح الشامل لـ {len(SHARIAH_STOCKS)} سهم...")
    stocks_data = fetch_all_data()
    market_trend = fetch_market_trend()

    analyzed = []
    latest_trading_date = None
    for name, data in stocks_data.items():
        hist = data["hist"]
        last_row_date = hist.index[-1].strftime("%Y-%m-%d")
        if latest_trading_date is None or last_row_date > latest_trading_date:
            latest_trading_date = last_row_date

        ind = compute_indicators(hist)
        fund = fetch_fundamentals(data["symbol"] + ".CA")

        tech_score, tech_tags = score_opportunity(ind)
        rev_score, rev_tags = score_reversal_opportunity(ind)
        fund_score, fund_tags = score_fundamentals(fund)

        alpha_score, alpha_tag = 0, None
        if market_trend:
            alpha_20d = ind["momentum_20d"] - market_trend["ind"]["momentum_20d"]
            if alpha_20d > 3:
                alpha_score, alpha_tag = 1, f"يتفوق على السوق بـ {alpha_20d:.1f}%"

        analyzed.append({
            "name": name, "symbol": data["symbol"], "ind": ind,
            "score": tech_score, "total_score": tech_score + fund_score + alpha_score,
            "fund_score": fund_score, "tags": tech_tags, "fund_tags": fund_tags, "alpha_tag": alpha_tag,
            "reversal_score": rev_score, "reversal_tags": rev_tags,
        })

    report_date = latest_trading_date or datetime.now().strftime("%Y-%m-%d")
    current_prices = {a["name"]: a["ind"]["last_close"] for a in analyzed}

    # --- فرص الزخم (نفس فلتر السيولة + التنويع القطاعي) ---
    candidates = [a for a in analyzed if a["score"] >= SCORE_THRESHOLD and a["ind"]["avg_daily_value"] >= MIN_LIQUIDITY]
    candidates.sort(key=lambda x: x["total_score"], reverse=True)
    candidates = candidates[:MAX_ALERTS]

    # --- فرص ارتداد ---
    reversal_candidates = [a for a in analyzed if a["reversal_score"] >= REVERSAL_THRESHOLD and a["ind"]["avg_daily_value"] >= MIN_LIQUIDITY]
    reversal_candidates.sort(key=lambda x: x["reversal_score"], reverse=True)
    reversal_candidates = reversal_candidates[:5]

    # --- الأكثر ارتفاعاً وانخفاضاً (يوم واحد) ---
    movers = sorted(analyzed, key=lambda x: x["ind"]["day_change_pct"], reverse=True)
    top_gainers = movers[:5]
    top_losers = movers[-5:][::-1]

    ws = get_worksheet()
    append_new_candidates_to_log(ws, candidates, report_date)
    check_hits_and_stops(ws, current_prices)

    # ============================================================
    # بناء الرسائل (كل قسم رسالة منفصلة)
    # ============================================================
    sections = []

    header = f"📈 <b>تقرير أسهم الشريعة الشامل</b>\nآخر يوم تداول مسجّل: {report_date}"
    if market_trend:
        header += f"\nالسوق العام (EGX30): {market_trend['label']}"
    sections.append(header)

    if candidates:
        lines = [f"🌟 <b>أفضل فرص الزخم</b> ({len(candidates)} فرصة، عتبة {SCORE_THRESHOLD}+)"]
        for c in candidates:
            ind = c["ind"]
            target = round(ind["last_close"] + 2 * ind["atr14"], 2)
            stop = round(ind["last_close"] - 1 * ind["atr14"], 2)
            ai_score_10 = round(min(c["total_score"] / 18 * 10, 10), 1)
            lines.append(
                f"🎯 <b>{c['name']}</b> ({c['symbol']}) - AI Score: {ai_score_10}/10\n"
                f"السعر: {ind['last_close']:.2f} | هدف: {target} | وقف: {stop}\n"
                f"{' | '.join(c['tags'][:3])}"
            )
        sections.append("\n\n".join(lines))
    else:
        sections.append(f"🌟 لا توجد فرص زخم قوية اليوم (عتبة {SCORE_THRESHOLD}+).")

    if reversal_candidates:
        lines = ["🔄 <b>فرص ارتداد محتملة (مخاطرة أعلى)</b>"]
        for a in reversal_candidates:
            ind = a["ind"]
            target = round(ind["last_close"] + 1.5 * ind["atr14"], 2)
            stop = round(ind["last_close"] - 0.8 * ind["atr14"], 2)
            lines.append(f"🔻 <b>{a['name']}</b> ({a['symbol']}) - {a['reversal_score']} نقطة\nالسعر: {ind['last_close']:.2f} | هدف: {target} | وقف ضيق: {stop}")
        sections.append("\n\n".join(lines))

    gainers_lines = ["📊 <b>الأكثر ارتفاعاً اليوم</b>"]
    for a in top_gainers:
        gainers_lines.append(f"🔥 {a['name']}: {a['ind']['day_change_pct']:+.2f}% ({a['ind']['last_close']:.2f} EGP)")
    gainers_lines.append("\n📊 <b>الأكثر انخفاضاً اليوم</b>")
    for a in top_losers:
        gainers_lines.append(f"🔻 {a['name']}: {a['ind']['day_change_pct']:+.2f}% ({a['ind']['last_close']:.2f} EGP)")
    sections.append("\n".join(gainers_lines))

    gold = fetch_gold_view()
    if gold:
        g_ind = gold["ind"]
        if gold["tech_score"] >= 4:
            view = "📈 اتجاه صاعد (زخم)"
        elif gold["rev_score"] >= 4:
            view = "🔄 بوادر ارتداد (مخاطرة أعلى)"
        else:
            view = "↔️ لا إشارة واضحة"
        sections.append(f"🥇 <b>الذهب العالمي</b>: {view}\n${g_ind['last_close']:,.1f}/أونصة ({g_ind['day_change_pct']:+.2f}%)")

    sections.append("⚠️ تحليل فني/أساسي آلي فقط - ليس توصية استثمارية مضمونة. راجع تلدا قبل التنفيذ.")

    send_report_sections(sections)
    print("انتهى المسح الشامل.")


if __name__ == "__main__":
    main()
