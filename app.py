import streamlit as st

import ccxt

import pandas as pd

import pandas_ta as ta

import time



# --- 1. 頁面配置 ---

st.set_page_config(

    page_title="Alpha Crypto Scanner",

    page_icon="🚀",

    layout="wide",

    initial_sidebar_state="expanded",

)



# --- 2. 樣式美化 (CSS) ---

st.markdown("""

<style>

    .big-font { font-size:24px !important; font-weight: bold; }

    .score-high { color: #10b981; font-size: 40px; font-weight: bold; }

    .score-mid { color: #f59e0b; font-size: 40px; font-weight: bold; }

    .score-low { color: #ef4444; font-size: 40px; font-weight: bold; }

    .stCard { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 10px; }

</style>

""", unsafe_allow_html=True)



# --- 3. 側邊欄配置 ---

st.sidebar.title("🎮 控制面板")

target_symbol = st.sidebar.text_input("輸入幣種 (例如: BTC, ETH, SOL)", "BTC").upper().strip()

exchange_id = st.sidebar.selectbox("選擇交易所", ["binance", "okx", "bybit"], index=0)

timeframe_tech = st.sidebar.selectbox("技術面時框", ["1d", "4h"], index=1)



# --- 4. 核心功能函數 ---



def get_technical_score(ex_id, symbol, timeframe):

    """獲取技術面評分與數據"""

    try:

        # 動態初始化交易所

        exchange_class = getattr(ccxt, ex_id)

        exchange = exchange_class()

        

        symbol_pair = f"{symbol}/USDT"

        # 獲取 OHLCV

        ohlcv = exchange.fetch_ohlcv(symbol_pair, timeframe=timeframe, limit=100)

        df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])

        

        score = 0

        details = []



        # A. 放量突破 (成交量 > 前 20 均值 2 倍)

        avg_vol = df['vol'].rolling(window=20).mean()

        curr_vol = df['vol'].iloc[-1]

        if curr_vol > (avg_vol.iloc[-1] * 2):

            score = 25

            details.append("⚡ 觸發放量突破 (C)")

        

        # B. 波動縮小 (VCP 形態簡易判斷)

        df['body_range'] = (df['close'] - df['open']).abs()

        is_vcp = all(df['body_range'].iloc[-i] < df['body_range'].iloc[-i-1] for i in range(1, 4))

        if is_vcp and score == 0:

            score = 25

            details.append("🌀 發現波動縮小 (VCP)")

            

        # C. 底部橫盤 (20 根 K 線波幅 < 10%)

        price_min = df['low'].tail(20).min()

        price_max = df['high'].tail(20).max()

        if (price_max - price_min) / price_min < 0.1 and score == 0:

            score = 25

            details.append("🛏️ 底部橫盤蓄勢")



        if not details:

            details.append("⚪ 技術面信號平淡")

            

        return score, details, df



    except Exception as e:

        return 0, [f"❌ 數據獲取失敗: {str(e)}"], None



def get_onchain_logic(symbol):

    """鏈上邏輯 (目前採模擬回傳，可串接 API)"""

    # 這裡預留給未來的 Arkham/Bubblemaps API

    outflow_score = 25 if symbol in ["BTC", "ETH", "SOL"] else 0

    conc_score = 25 if len(symbol) > 3 else 0 # 假設山寨幣集中度高

    mm_score = 25 if symbol in ["PEPE", "WIF"] else 0

    return outflow_score, conc_score, mm_score



# --- 5. 主頁面渲染 ---

st.title("🛡️ 加密貨幣多維度全自動評分系統")

st.divider()



# 計算評分

with st.spinner('正在掃描鏈上與技術面數據...'):

    t_score, t_details, df_data = get_technical_score(exchange_id, target_symbol, timeframe_tech)

    o_score, c_score, m_score = get_onchain_logic(target_symbol)

    total_score = t_score + o_score + c_score + m_score



# 展示總分

score_color = "score-low"

if total_score >= 75: score_color = "score-high"

elif total_score >= 50: score_color = "score-mid"



st.markdown(f"""

<div class='stCard' style='text-align: center;'>

    <div class='big-font'>{target_symbol} 綜合評分</div>

    <div class='{score_color}'>{total_score} / 100</div>

</div>

""", unsafe_allow_html=True)



# 四大維度卡片

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.info(f"**技術蓄勢**\n\n得分: {t_score}\n\n{t_details[0]}")

with col2:

    st.info(f"**交易所缺貨**\n\n得分: {o_score}\n\n30D 淨流出監控")

with col3:

    st.info(f"**持倉集中度**\n\n得分: {conc_score}\n\nTop 10 佔比監控")

with col4:

    st.info(f"**MM 人造繁榮**\n\n得分: {m_score}\n\n機器人集群監控")



# --- 6. TradingView 圖表嵌入 ---

st.subheader(f"📈 {target_symbol} 實時圖表預覽")

tv_symbol = f"{exchange_id.upper()}:{target_symbol}USDT"

tv_html = f"""

    <div style="height:500px;">

        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>

        <script type="text/javascript">

        new TradingView.widget({{

          "autosize": true, "symbol": "{tv_symbol}", "interval": "240",

          "timezone": "Etc/UTC", "theme": "dark", "style": "1",

          "locale": "zh_TW", "enable_publishing": false, "container_id": "tv_chart"

        }});

        </script>

        <div id="tv_chart" style="height:100%;"></div>

    </div>

"""

st.components.v1.html(tv_html, height=500)



st.caption("備註：鏈上數據維度目前為邏輯模擬，需對接 Arkham/Dune API 以獲得實時數據。")
