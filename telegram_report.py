"""
تقرير يومي أوتوماتيك على تليجرام - أسهم الشريعة الإسلامية EGX
يعمل بشكل مستقل عن تطبيق Streamlit، مصمم ليُشغَّل يومياً عبر GitHub Actions.
لا يحتوي على أي Token داخل الكود - كل البيانات الحساسة تُقرأ من متغيرات البيئة (GitHub Secrets).
"""

import os
import requests
import yfinance as yf
import pandas as pd
import numpy as np

# --- قائمة الأسهم المتوافقة مع الشريعة (نفس القائمة الأصلية بدون أي تعديل) ---
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
    "سيدي كرير للبتروكيماويات": "SKPC.CA",
}


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

    return {
        "last_close": last_close, "day_change_pct": day_change_pct, "sma20": sma20, "sma50": sma50,
        "rsi14": rsi14, "atr14": atr14, "momentum_5d": momentum_5d, "momentum_20d": momentum_20d,
        "vol_ratio": vol_ratio, "high_52w": high_52w, "low_52w": low_52w, "pct_from_high": pct_from_high,
        "avg_daily_value": avg_daily_value, "weekly_confirmed": weekly_confirmed,
    }


def score_opportunity(ind):
    score, tags = 0, []
    if ind["last_close"] > ind["sma20"] > ind["sma50"]:
        score += 3; tags.append("اتجاه صاعد مؤكد")
    elif ind["last_close"] > ind["sma20"]:
        score += 1; tags.append("فوق المتوسط قصير المدى")
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
    return score, tags


def fetch_all_data():
    results = {}
    for name, symbol in SHARIAH_STOCKS.items():
        try:
            hist = yf.Ticker(symbol).history(period="4mo", interval="1d")
            if hist.empty or len(hist) < 35:
                continue
            results[name] = {"symbol": symbol.replace(".CA", ""), "hist": hist}
        except Exception:
            continue
    return results


def fetch_gold_view():
    try:
        hist = yf.Ticker("GC=F").history(period="4mo", interval="1d")
        if hist.empty or len(hist) < 35:
            return None
        ind = compute_indicators(hist)
        score, tags = score_opportunity(ind)
        return {"ind": ind, "score": score, "tags": tags}
    except Exception:
        return None


def build_report():
    stocks_data = fetch_all_data()
    analyzed = []
    for name, data in stocks_data.items():
        ind = compute_indicators(data["hist"])
        score, tags = score_opportunity(ind)
        analyzed.append({"name": name, "symbol": data["symbol"], "ind": ind, "score": score, "tags": tags})

    candidates = [a for a in analyzed if a["score"] >= 5]
    candidates.sort(key=lambda x: x["score"], reverse=True)
    candidates = candidates[:5]

    lines = ["📈 *تقرير أسهم الشريعة الإسلامية - EGX*\n"]

    if candidates:
        lines.append("🌟 *أفضل الفرص اليوم (تحليل فني):*")
        for c in candidates:
            ind = c["ind"]
            target = ind["last_close"] + 2 * ind["atr14"]
            stop = ind["last_close"] - 1 * ind["atr14"]
            lines.append(
                f"• *{c['name']}* ({c['symbol']}) - {c['score']} نقطة\n"
                f"  السعر: {ind['last_close']:.2f} EGP ({ind['day_change_pct']:+.2f}%)\n"
                f"  هدف: {target:.2f} | وقف: {stop:.2f}"
            )
    else:
        lines.append("لا توجد فرص قوية (≥5 نقاط) اليوم حسب معايير التحليل الفني.")

    gold = fetch_gold_view()
    if gold:
        g_ind = gold["ind"]
        view = "صاعد" if gold["score"] >= 4 else "متذبذب/بلا إشارة واضحة"
        lines.append(f"\n🥇 *الذهب العالمي:* {view} - ${g_ind['last_close']:,.1f}/أونصة ({g_ind['day_change_pct']:+.2f}%)")

    lines.append("\n⚠️ تحليل فني آلي فقط - ليس توصية استثمارية مضمونة. راجع تطبيق تلدا قبل أي تنفيذ.")
    return "\n".join(lines)


def send_telegram_message(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # تليجرام بيحدد طول الرسالة بـ 4096 حرف - نقسم لو المحتوى أطول
    max_len = 4000
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)] or [text]
    for chunk in chunks:
        resp = requests.post(url, json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"}, timeout=30)
        if resp.status_code != 200:
            print("فشل إرسال الرسالة:", resp.text)


if __name__ == "__main__":
    report = build_report()
    send_telegram_message(report)
    print("تم إرسال التقرير بنجاح.")
