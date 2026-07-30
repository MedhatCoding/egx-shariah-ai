import streamlit as st
import google.generativeai as genai
import yfinance as ticker_fetcher
import pandas as pd
from datetime import datetime

# 1. إعداد الصفحة
st.set_page_config(
    page_title="منصة تحليل أسهم الشريعة | EGX 33 Shariah",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنسيق CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #059669;
        text-align: center;
        font-weight: bold;
        margin-bottom: 0.3rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🟢 منصة تحليل مؤشر الشريعة المتقدمة (EGX 33)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">تغطية شاملة لجميع الـ 33 سهم المعتمدة شرعياً في البورصة المصرية مع تحليل لحظي ودعم الأخبار</div>', unsafe_allow_html=True)

# 2. جلب الـ API Key من Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("⚠️ لم يتم العثور على `GEMINI_API_KEY` في ملف Streamlit Secrets!")
    st.stop()

# 3. القائمة الكاملة والمعتمدة رسمياً لمكونات مؤشر الشريعة بالبورصة المصرية
SHARIAH_COMPLIANT_STOCKS = {
    "مصرف أبو ظبي الإسلامي - مصر (ADIB.CA)": "ADIB.CA",
    "بنك البركة مصر (SAUD.CA)": "SAUD.CA",
    "بنك فيصل الإسلامي - جنيه (FAIT.CA)": "FAIT.CA",
    "بنك فيصل الإسلامي - دولار (FAITA.CA)": "FAITA.CA",
    "أبو قير للأسمدة (ABUK.CA)": "ABUK.CA",
    "أموك - الإسكندرية للزيوت (AMOC.CA)": "AMOC.CA",
    "موبكو - مصر للإنتاج المزدوج (MFPC.CA)": "MFPC.CA",
    "سيدي كرير للبتروكيماويات - سيدبك (SKPC.CA)": "SKPC.CA",
    "الدولية للأسمدة والكيماويات (ICFC.CA)": "ICFC.CA",
    "السويدي إلكتريك (SWDY.CA)": "SWDY.CA",
    "مجموعة طلعت مصطفى القابضة (TMGH.CA)": "TMGH.CA",
    "سوديك - السادس من أكتوبر (OCDI.CA)": "OCDI.CA",
    "بالم هيلز للتعمير (PHDC.CA)": "PHDC.CA",
    "مدينة مصر للإسكان والتعمير (MASR.CA)": "MASR.CA",
    "إعمار مصر للتنمية (EMFD.CA)": "EMFD.CA",
    "أوراسكوم للتنمية مصر (ORHD.CA)": "ORHD.CA",
    "فوري للمدفوعات الإلكترونية (FWRY.CA)": "FWRY.CA",
    "إي فاينانس للاستثمارات (EFIH.CA)": "EFIH.CA",
    "المصرية للاتصالات (ETEL.CA)": "ETEL.CA",
    "جهينة للصناعات الغذائية (JUFO.CA)": "JUFO.CA",
    "إيديتا للصناعات الغذائية (EFID.CA)": "EFID.CA",
    "عبور لاند للصناعات الغذائية (OLFI.CA)": "OLFI.CA",
    "المنصورة للدواجن (MPCO.CA)": "MPCO.CA",
    "مصر للجلاد والبروفايل - ليسيكو (LCSW.CA)": "LCSW.CA",
    "العربية للأسمنت (ARCC.CA)": "ARCC.CA",
    "مصر للأسمنت - قنا (MCQE.CA)": "MCQE.CA",
    "مصر للالومنيوم (EGAL.CA)": "EGAL.CA",
    "مصر الوطنية للصلب - عتاقة (ATQA.CA)": "ATQA.CA",
    "أوراسكوم كونستراكشون بي ال سي (ORAS.CA)": "ORAS.CA",
    "النساجون الشرقيون للسجاد (ORWE.CA)": "ORWE.CA",
    "ابن سينا فارما (ISPH.CA)": "ISPH.CA",
    "العاشر من رمضان - راميدا (RMDA.CA)": "RMDA.CA",
    "مستشفى كليوباترا (CLHO.CA)": "CLHO.CA",
    "العربية لحليج الأقطان (ACGC.CA)": "ACGC.CA",
    "غاز مصر (EGAS.CA)": "EGAS.CA",
    "ام.ام جروب للصناعة (MTIE.CA)": "MTIE.CA",
    "راية لخدمات مراكز الاتصالات (RACC.CA)": "RACC.CA",
    "راية القابضة للاستثمارات (RAYA.CA)": "RAYA.CA",
    "المصرية لخدمات النقل - إيجيترانس (ETRS.CA)": "ETRS.CA",
    "تعليم لخدمات الإدارة (TALM.CA)": "TALM.CA",
    "الدولية للمحاصيل الزراعية (IFAP.CA)": "IFAP.CA",
    "القاهرة للاستثمار - سيرا (CIRA.CA)": "CIRA.CA"
}

# 4. القائمة الجانبية
with st.sidebar:
    st.header("⚙️ خيارات السهم الشرعي")
    selected_stock_label = st.selectbox("اختر السهم من قائمة مؤشر الشريعة:", list(SHARIAH_COMPLIANT_STOCKS.keys()))
    ticker_symbol = SHARIAH_COMPLIANT_STOCKS[selected_stock_label]
    
    st.success(f"✓ السهم محدد: {ticker_symbol}")

# 5. جلب بيانات السهم والأخبار لحظياً مع التخزين المؤقت
@st.cache_data(ttl=600)
def fetch_stock_data_and_news(symbol):
    try:
        stock = ticker_fetcher.Ticker(symbol)
        hist = stock.history(period="1mo")
        if hist.empty:
            return None, None, "لم يتم العثور على حركة أسعار لحظية لهذا السهم."
        
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        news = stock.news
        news_summary = []
        if news:
            for item in news[:3]:
                news_summary.append(f"- {item.get('title', '')}")
        news_text = "\n".join(news_summary) if news_summary else "لا توجد أخبار جوهرية مباشرة مسجلة لحظياً."
        
        data_summary = {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "change_pct": round(change_pct, 2),
            "high": round(hist['High'].max(), 2),
            "low": round(hist['Low'].min(), 2),
            "volume": int(hist['Volume'].iloc[-1]),
            "history_tail": hist.tail(5)[['Open', 'High', 'Low', 'Close', 'Volume']].to_string()
        }
        
        return data_summary, news_text, None
    except Exception as e:
        return None, None, str(e)

# 6. عرض النتائج والتقرير
data_summary, news_text, error = fetch_stock_data_and_news(ticker_symbol)

if error:
    st.error(f"حدث خطأ أثناء جلب بيانات السهم: {error}")
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("السهم الشرعي", selected_stock_label)
    col2.metric("السعر اللحظي (EGP)", f"{data_summary['current_price']}", f"{data_summary['change_pct']}%")
    col3.metric("حجم تداول آخر جلسة", f"{data_summary['volume']:,}")

    st.markdown("---")
    
    with st.expander("📰 أحدث الأخبار والتحركات اللحظية المجلوبة السريعة"):
        st.write(news_text)

    if st.button("🚀 إصدار التقرير الشرعي والفني الشامل", use_container_width=True):
        with st.spinner("جاري تحليل بيانات السهم الفنية والأخبار بواسطة الذكاء الاصطناعي..."):
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                prompt = f"""
                أنت خبير ماليات ومحلل أسواق متمرس في البورصة المصرية (EGX) ومؤشر الشريعة الإسلامية.
                قم بكتابة تقرير استثماري احترافي ودقيق للسهم المختار والمدرج ضمن مؤشر الشريعة:
                
                بيانات السهم اللحظية:
                - السهم: {selected_stock_label} ({data_summary['symbol']})
                - السعر الحالي: {data_summary['current_price']} جنيه
                - نسبة التغير اليومي: {data_summary['change_pct']}%
                - أعلى سعر (خلال شهر): {data_summary['high']} | أدنى سعر: {data_summary['low']}
                - حجم التداول: {data_summary['volume']}
                - حركة آخر 5 جلسات:
                {data_summary['history_tail']}
                
                الأخبار اللحظية المتعلقة:
                {news_text}
                
                المطلوب: صياغة تقرير استثماري محترف ومباشر يشتمل على البنود التالية بوضوح:
                1. **تأكيد التوافق الشرعي**: إشارة موجزة حول إدراج السهم بمؤشر الشريعة EGX 33.
                2. **تقييم الفرصة الاستثمارية**: (فرصة ممتازة للشراء / شراء بحذر / انتظار وتحين فرصة).
                3. **سعر الشراء المقترح (Entry Price)**.
                4. **السعر المستهدف (Target Price)**.
                5. **نسبة الربح المتوقعة (%)**.
                6. **وقف الخسارة (Stop Loss)**.
                7. **أسباب التحليل**: (تجميع التحليل الفني للأسعار السابقة مع تأثير الأخبار اللحظية).
                """
                
                response = model.generate_content(prompt)
                
                st.markdown("### 📋 التقرير الاستثماري الشرعي النهائي")
                st.info(f"تاريخ ووقت التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"حدث خطأ أثناء طلب التقرير: {e}")
        
