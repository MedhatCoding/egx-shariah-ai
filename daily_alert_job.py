# -*- coding: utf-8 -*-
"""
سكريبت مستقل (من غير Streamlit) بيعمل مسح يومي لأسهم الشريعة، يسجل الفرص في Google Sheets،
ويبعت ملخص فوري على تليجرام. مصمم عشان يتشغّل تلقائياً عن طريق GitHub Actions (مجاني)
في وقت محدد كل يوم، حتى لو التطبيق نفسه (Streamlit) مقفول.

كل الإعدادات بتتقرأ من متغيرات البيئة (Environment Variables) اللي بيوفرها GitHub Actions
من الـ Secrets بتاعة الريبو، مش من st.secrets زي التطبيق.
"""

import os
import json
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime

# ============================================================
# 1) قائمة الأسهم (نفس قائمة التطبيق بالظبط)
# ============================================================
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
    "بنك فيصل الإسلامي المصري - بالجنيه": "FAIT.CA",
}

SCORE_THRESHOLD = int(os.environ.get("SCORE_THRESHOLD", "5"))  # صرامة الفلتر (زي الشريحة في التطبيق)
MAX_ALERTS = 8  # أقصى عدد فرص تتبعت في رسالة تليجرام الواحدة

LOG_COLUMNS = ["التاريخ", "السهم", "الرمز", "سعر الدخول", "الهدف", "وقف الخسارة", "النقاط", "سبب الدخول", "نُفّذت فعلاً؟", "تم التنبيه؟"]


# ============================================================
# 2) نفس حسابات المؤشرات الفنية والتسجيل الموجودة في التطبيق (بدون أي تغيير في المنطق)
# ============================================================
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

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    rsi14 = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else 50.0

    prev_close_series = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close_series).abs(),
        (low - prev_close_series).abs()
    ], axis=1).max(axis=1)
    atr14 = float(tr.rolling(14).mean().iloc[-1])

    momentum_5d = ((last_close - float(close.iloc[-6])) / float(close.iloc[-6])) * 100 if len(close) > 6 else 0.0
    momentum_20d = ((last_close - float(close.iloc[-21])) / float(close.iloc[-21])) * 100 if len(close) > 21 else 0.0

    avg_vol20 = float(volume.rolling(20).mean().iloc[-1])
    last_vol = float(volume.iloc[-1])
    vol_ratio = (last_vol / avg_vol20) if avg_vol20 > 0 else 1.0

    high_52w = float(high.max())
    low_52w = float(low.min())
    pct_from_high = ((last_close - high_52w) / high_52w) * 100
    avg_daily_value = avg_vol20 * last_close

    weekly_confirmed = False
    try:
        weekly_close = close.resample("W").last().dropna()
        if len(weekly_close) >= 5:
            wma4 = weekly_close.rolling(4).mean().iloc[-1]
            weekly_confirmed = bool(weekly_close.iloc[-1] > wma4)
    except Exception:
        weekly_confirmed = False

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
    score = 0
    tags = []
    if ind["last_close"] > ind["sma20"] > ind["sma50"]:
        score += 3
        tags.append("اتجاه صاعد مؤكد (فوق المتوسطين)")
    elif ind["last_close"] > ind["sma20"]:
        score += 1
        tags.append("فوق المتوسط قصير المدى")
    if ind["momentum_5d"] > 4:
        score += 2
        tags.append("زخم قوي خلال 5 جلسات")
    elif ind["momentum_5d"] > 1:
        score += 1
        tags.append("زخم إيجابي قصير المدى")
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
    if ind["vol_ratio"] > 1.8:
        score += 2
        tags.append(f"سيولة استثنائية ({ind['vol_ratio']:.1f}x المتوسط)")
    elif ind["vol_ratio"] > 1.3:
        score += 1
        tags.append(f"سيولة أعلى من المعتاد ({ind['vol_ratio']:.1f}x)")
    if ind["pct_from_high"] > -8:
        score += 1
        tags.append("قريب من أعلى مستوياته")
    if ind.get("weekly_confirmed"):
        score += 1
        tags.append("الاتجاه الأسبوعي يؤكد الصعود")
    if ind.get("adx14", 0) >= 25:
        score += 1
        tags.append(f"اتجاه قوي مؤكد (ADX {ind['adx14']:.0f})")
    return score, tags


# ============================================================
# 3) تليجرام
# ============================================================
def send_telegram_message(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID غير موجودين - تم تخطي إرسال تليجرام.")
        return False
    import requests
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=15)
        r.raise_for_status()
        return True
    except Exception as e:
        print("⚠️ فشل إرسال تليجرام:", e)
        return False


# ============================================================
# 4) Google Sheets - يسجل التوصيات الجديدة في نفس شيت التطبيق (تبويب "log")
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


def append_new_candidates_to_log(ws, candidates):
    if ws is None or not candidates:
        return
    try:
        records = ws.get_all_records()
        existing = {(r.get("التاريخ"), r.get("السهم")) for r in records}
    except Exception as e:
        print("⚠️ تعذرت قراءة السجل الحالي:", e)
        existing = set()

    today = datetime.now().strftime("%Y-%m-%d")
    new_rows = []
    for c in candidates:
        if (today, c["name"]) in existing:
            continue
        ind = c["ind"]
        new_rows.append([
            today, c["name"], c["symbol"],
            round(ind["last_close"], 2),
            round(ind["last_close"] + 2 * ind["atr14"], 2),
            round(ind["last_close"] - 1 * ind["atr14"], 2),
            c["score"], " | ".join(c["tags"])[:200],
            False, False,
        ])
    if new_rows:
        try:
            ws.append_rows(new_rows, value_input_option="USER_ENTERED")
            print(f"✅ تم تسجيل {len(new_rows)} توصية جديدة في Google Sheets.")
        except Exception as e:
            print("⚠️ تعذر إضافة الصفوف الجديدة:", e)


def check_hits_and_stops(ws, current_prices: dict):
    """
    يقرأ السجل الحالي كامل، ويفحص كل توصية لسه ماتنبّهناش عليها (تم التنبيه؟ = False):
    لو السعر الحالي وصل الهدف أو ضرب وقف الخسارة، يبعت رسالة تليجرام ويعلّم الصف كـ "تم التنبيه؟ = True".
    """
    if ws is None:
        return
    try:
        records = ws.get_all_records()
    except Exception as e:
        print("⚠️ تعذرت قراءة السجل لفحص الأهداف/الوقف:", e)
        return
    if not records:
        return

    rows_to_update = []  # (row_index_في_الشيت, message)
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
            msg = f"✅ <b>{name}</b>: تحقق الهدف عند {target} EGP (السعر الحالي {current:.2f})"
            rows_to_update.append((i + 2, msg))  # +2: صف العناوين + فهرسة تبدأ من 1
        elif current <= stop:
            msg = f"❌ <b>{name}</b>: ضرب وقف الخسارة عند {stop} EGP (السعر الحالي {current:.2f})"
            rows_to_update.append((i + 2, msg))

    if not rows_to_update:
        return

    notified_col_index = LOG_COLUMNS.index("تم التنبيه؟") + 1  # gspread أعمدته تبدأ من 1
    for row_num, msg in rows_to_update:
        if send_telegram_message(msg):
            try:
                ws.update_cell(row_num, notified_col_index, True)
            except Exception as e:
                print("⚠️ تعذر تحديث عمود التنبيه:", e)
    print(f"🔔 تم إرسال {len(rows_to_update)} تنبيه هدف/وقف خسارة.")


# ============================================================
# 5) التشغيل الرئيسي
# ============================================================
def main():
    print(f"[{datetime.now()}] بدء المسح اليومي لـ {len(SHARIAH_STOCKS)} سهم...")
    candidates = []
    current_prices = {}
    failed = []

    for name, symbol in SHARIAH_STOCKS.items():
        try:
            hist = yf.Ticker(symbol).history(period="1y", interval="1d")
            if hist.empty or len(hist) < 60:
                failed.append(name)
                continue
            ind = compute_indicators(hist)
            current_prices[name] = ind["last_close"]  # نخزن سعر كل الأسهم (مش الفرص بس) عشان فحص الهدف/الوقف
            score, tags = score_opportunity(ind)
            if score >= SCORE_THRESHOLD:
                candidates.append({
                    "name": name, "symbol": symbol.replace(".CA", ""),
                    "ind": ind, "score": score, "tags": tags,
                })
        except Exception as e:
            failed.append(name)
            continue

    candidates.sort(key=lambda x: x["score"], reverse=True)
    print(f"تم العثور على {len(candidates)} فرصة (بعتبة {SCORE_THRESHOLD} نقطة) من أصل {len(SHARIAH_STOCKS) - len(failed)} سهم تم تحليلها.")

    # سجّل الفرص الجديدة في نفس شيت السجل بتاع التطبيق (لو معدّة)
    ws = get_worksheet()
    append_new_candidates_to_log(ws, candidates)

    # افحص التوصيات القديمة في السجل: هل وصلت هدفها أو ضربت وقفها؟ (وابعت تنبيه فوري لو كده)
    check_hits_and_stops(ws, current_prices)

    # ابعت ملخص تليجرام يومي بالفرص الجديدة
    today_str = datetime.now().strftime("%Y-%m-%d")
    if not candidates:
        msg = f"📅 {today_str}\nمفيش فرص وصلت لعتبة {SCORE_THRESHOLD} نقطة النهاردة."
    else:
        lines = [f"📊 <b>ملخص فرص اليوم - {today_str}</b>", f"({len(candidates)} فرصة بعتبة {SCORE_THRESHOLD}+ نقطة)\n"]
        for c in candidates[:MAX_ALERTS]:
            ind = c["ind"]
            target = round(ind["last_close"] + 2 * ind["atr14"], 2)
            stop = round(ind["last_close"] - 1 * ind["atr14"], 2)
            lines.append(
                f"🎯 <b>{c['name']}</b> ({c['symbol']})\n"
                f"السعر: {ind['last_close']:.2f} | الهدف: {target} | وقف الخسارة: {stop} | النقاط: {c['score']}"
            )
        if len(candidates) > MAX_ALERTS:
            lines.append(f"\n...و{len(candidates) - MAX_ALERTS} فرصة تانية، افتح التطبيق لمتابعتها بالكامل.")
        msg = "\n\n".join(lines)

    send_telegram_message(msg)
    print("انتهى المسح اليومي.")


if __name__ == "__main__":
    main()
    
