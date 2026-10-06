import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="TENJO 14:15", page_icon="📈", layout="wide")
st.title("TENJO｜14:15 日股尾盘埋伏筛选")
st.caption("日股限定｜盘中价格・成交量・振幅・位置评分｜新闻只作风险提示")

DEFAULT = """627A
5801
6203
8267"""

with st.sidebar:
    st.header("候选池")
    raw = st.text_area("每行一个日本股票代码", DEFAULT, height=220)
    st.caption("5801 会自动识别为 5801.T；美股会被排除。")
    run = st.button("开始筛选", type="primary", use_container_width=True)

def jp(x):
    x = x.strip().upper()
    if x.endswith(".T"):
        return x
    if len(x) == 4 and x.isalnum() and any(c.isdigit() for c in x):
        return x + ".T"
    return None

@st.cache_data(ttl=60)
def load(ticker):
    t = yf.Ticker(ticker)
    intra = t.history(period="5d", interval="5m", auto_adjust=False)
    daily = t.history(period="3mo", interval="1d", auto_adjust=False)
    try:
        news = t.news[:5]
    except Exception:
        news = []
    return intra, daily, news

def calc(ticker):
    intra, daily, news = load(ticker)
    if intra.empty or daily.empty:
        return None

    day = intra.index[-1].date()
    d = intra[intra.index.date == day]
    if d.empty:
        d = intra.tail(60)

    last = float(d.Close.iloc[-1])
    op = float(d.Open.iloc[0])
    hi = float(d.High.max())
    lo = float(d.Low.min())
    vol = float(d.Volume.sum())
    prev = float(daily.Close.iloc[-2]) if len(daily) > 1 else op

    pct = (last / prev - 1) * 100 if prev else 0
    rng = (hi / lo - 1) * 100 if lo else 0
    pos = (last - lo) / (hi - lo) if hi > lo else .5

    base = float(daily.Volume.tail(21).iloc[:-1].mean()) if len(daily) > 1 else max(vol, 1)
    vr = vol / base if base else 0

    ma5 = float(daily.Close.tail(5).mean())
    ma20 = float(daily.Close.tail(20).mean())
    low20 = float(daily.Low.tail(20).min())
    high20 = float(daily.High.tail(20).max())
    loc20 = (last - low20) / (high20 - low20) if high20 > low20 else .5

    # 偏向“尾盘低位埋伏但仍有活性”的候选，而不是单纯追涨。
    s = 50 + min(rng, 12) * 2 + min(vr, 3) * 7 + (0.55 - abs(pos - .45)) * 18
    if -4 <= pct <= 1.5:
        s += 8
    if pct < -7:
        s -= 18
    if pos < .12:
        s -= 8
    if vr < .25:
        s -= 15
    if last > ma5:
        s += 5
    if ma5 > ma20:
        s += 4
    if loc20 < .25:
        s += 4

    s = round(max(0, min(100, s)), 1)

    heads = []
    for n in news:
        c = n.get("content", n)
        if isinstance(c, dict) and c.get("title"):
            heads.append(c["title"])

    return {
        "代码": ticker[:-2],
        "现价": round(last, 1),
        "当日%": round(pct, 2),
        "日内低": round(lo, 1),
        "日内高": round(hi, 1),
        "振幅%": round(rng, 2),
        "量比(粗略)": round(vr, 2),
        "区间位置": round(pos, 2),
        "20日位置": round(loc20, 2),
        "评分": s,
        "新闻": " / ".join(heads[:2]) or "暂无可用标题",
    }

if run:
    codes, bad = [], []
    for x in raw.replace(",", "\n").splitlines():
        if not x.strip():
            continue
        t = jp(x)
        (codes if t else bad).append(t or x.strip())

    codes = list(dict.fromkeys(codes))

    if bad:
        st.warning("已排除非日股/格式不符：" + ", ".join(bad))

    rows = []
    for t in codes:
        try:
            r = calc(t)
            if r:
                rows.append(r)
        except Exception as e:
            st.warning(f"{t} 数据失败：{e}")

    if rows:
        df = pd.DataFrame(rows).sort_values("评分", ascending=False).reset_index(drop=True)
        now = datetime.now(ZoneInfo("Asia/Tokyo"))
        st.subheader("筛选结果｜" + now.strftime("%Y-%m-%d %H:%M JST"))
        st.dataframe(df.drop(columns=["新闻"]), use_container_width=True, hide_index=True)

        b = df.iloc[0]
        st.success(
            f"当前第一候选：{b['代码']}｜评分 {b['评分']}｜"
            f"现价 {b['现价']}｜日内 {b['日内低']}–{b['日内高']}"
        )
        st.info("评分偏向：仍有成交和振幅、没有追在日内最高位，同时避免明显自由落体。14:15 左右运行最符合用途。")

        st.subheader("新闻风险提示")
        for _, r in df.iterrows():
            with st.expander(f"{r['代码']}｜评分 {r['评分']}"):
                st.write(r["新闻"])
    else:
        st.error("没有取得可用行情。")
else:
    st.info("把候选日股代码放左侧，14:15 左右点「开始筛选」。")

st.caption("公开行情可能延迟或缺失。本工具用于筛选，不保证次日上涨，也不能精准预测次日最高/最低价。")
