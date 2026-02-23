import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# 页面设置
st.set_page_config(
    page_title="财务突破系统 V2.0 - 实时股票分析",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("📈 财务突破系统 V2.0")
st.markdown("实时获取贵州茅台、泸州老窖等A股数据")

# 股票代码映射
STOCK_MAP = {
    "贵州茅台": {"code": "600519", "symbol": "600519.SH"},
    "泸州老窖": {"code": "000568", "symbol": "000568.SZ"},
    "五粮液": {"code": "000858", "symbol": "000858.SZ"}
}

# 缓存函数：获取实时行情
@st.cache_data(ttl=60)  # 60秒缓存
def get_realtime_quotes():
    """获取所有股票的实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        # 筛选我们关注的股票
        target_codes = [STOCK_MAP[s]["code"] for s in STOCK_MAP]
        df = df[df["代码"].isin(target_codes)]
        
        # 重命名列
        columns_map = {
            "代码": "code",
            "名称": "name",
            "最新价": "latest_price",
            "涨跌额": "change_amount",
            "涨跌幅": "change_percent",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "最高": "high",
            "最低": "low",
            "今开": "open",
            "昨收": "prev_close",
            "换手率": "turnover_rate"
        }
        df = df.rename(columns=columns_map)
        return df
    except Exception as e:
        st.error(f"获取实时行情失败: {str(e)}")
        return pd.DataFrame()

# 缓存函数：获取历史K线数据
@st.cache_data(ttl=300)  # 5分钟缓存
def get_historical_data(stock_code, days=30):
    """获取历史K线数据"""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 使用akshare获取日K数据
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="qfq"  # 前复权
        )
        
        if not df.empty:
            # 格式化列名
            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "pct_change",
                "涨跌额": "change",
                "换手率": "turnover"
            })
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        return df
    except Exception as e:
        st.warning(f"获取{stock_code}历史数据失败: {str(e)}")
        return pd.DataFrame()

# 缓存函数：获取资金流向
@st.cache_data(ttl=300)
def get_money_flow(stock_code):
    """获取个股资金流向"""
    try:
        df = ak.stock_individual_fund_flow(stock=stock_code, market="SZ" if stock_code.startswith("0") else "SH")
        return df.head(10)  # 返回最近10天的数据
    except:
        return pd.DataFrame()

# 侧边栏配置
st.sidebar.header("📊 股票选择")
selected_stocks = st.sidebar.multiselect(
    "选择关注的股票",
    list(STOCK_MAP.keys()),
    default=["贵州茅台", "泸州老窖", "五粮液"]
)

# 分析周期
analysis_days = st.sidebar.slider("分析周期(天)", 7, 365, 30)

# 显示样式
show_charts = st.sidebar.checkbox("显示图表", True)
show_details = st.sidebar.checkbox("显示详细数据", True)

# 主页面
if selected_stocks:
    # 1. 实时行情展示
    st.header("📊 实时行情")
    
    realtime_data = get_realtime_quotes()
    
    if not realtime_data.empty:
        # 筛选选择的股票
        selected_codes = [STOCK_MAP[s]["code"] for s in selected_stocks]
        display_df = realtime_data[realtime_data["code"].isin(selected_codes)].copy()
        
        # 格式化显示
        display_df["涨跌幅"] = (display_df["change_percent"] * 100).round(2).astype(str) + "%"
        display_df["最新价"] = display_df["latest_price"].round(2)
        display_df["成交量(万)"] = (display_df["volume"] / 10000).round(2)
        display_df["成交额(亿)"] = (display_df["amount"] / 100000000).round(3)
        
        # 重排序列
        display_columns = ["name", "latest_price", "change_percent", "change_amount", 
                          "volume", "amount", "open", "high", "low", "prev_close", 
                          "amplitude", "turnover_rate"]
        
        # 显示表格
        st.dataframe(
            display_df[["name", "latest_price", "change_percent", "volume", "amount"]].rename(columns={
                "name": "股票名称",
                "latest_price": "最新价",
                "change_percent": "涨跌幅",
                "volume": "成交量",
                "amount": "成交额"
            }),
            use_container_width=True,
            height=200
        )
        
        # 2. K线图展示
        if show_charts:
            st.header("📈 K线走势图")
            
            for stock_name in selected_stocks:
                stock_info = STOCK_MAP[stock_name]
                hist_data = get_historical_data(stock_info["code"], analysis_days)
                
                if not hist_data.empty:
                    with st.expander(f"{stock_name} ({stock_info['code']})"):
                        # 创建K线图
                        fig = make_subplots(
                            rows=2, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.1,
                            row_heights=[0.7, 0.3],
                            subplot_titles=(f"{stock_name} K线图", "成交量")
                        )
                        
                        # 添加K线
                        fig.add_trace(
                            go.Candlestick(
                                x=hist_data['date'],
                                open=hist_data['open'],
                                high=hist_data['high'],
                                low=hist_data['low'],
                                close=hist_data['close'],
                                name="K线"
                            ),
                            row=1, col=1
                        )
                        
                        # 添加成交量
                        colors = ['red' if row['close'] >= row['open'] else 'green' 
                                 for _, row in hist_data.iterrows()]
                        
                        fig.add_trace(
                            go.Bar(
                                x=hist_data['date'],
                                y=hist_data['volume'],
                                name="成交量",
                                marker_color=colors
                            ),
                            row=2, col=1
                        )
                        
                        # 更新布局
                        fig.update_layout(
                            height=600,
                            showlegend=False,
                            xaxis_rangeslider_visible=False
                        )
                        
                        fig.update_xaxes(title_text="日期", row=2, col=1)
                        fig.update_yaxes(title_text="价格", row=1, col=1)
                        fig.update_yaxes(title_text="成交量", row=2, col=1)
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 显示关键指标
                        col1, col2, col3, col4 = st.columns(4)
                        latest = hist_data.iloc[-1]
                        
                        with col1:
                            st.metric("最新价", f"¥{latest['close']:.2f}")
                        with col2:
                            change_pct = ((latest['close'] - hist_data.iloc[-2]['close']) / hist_data.iloc[-2]['close'] * 100)
                            st.metric("日涨跌", f"{change_pct:.2f}%", 
                                     delta_color="inverse" if change_pct < 0 else "normal")
                        with col3:
                            st.metric("成交量", f"{latest['volume']/10000:.1f}万手")
                        with col4:
                            st.metric("成交额", f"{latest['amount']/100000000:.2f}亿元")
        
        # 3. 详细数据
        if show_details:
            st.header("📋 详细数据")
            
            for stock_name in selected_stocks:
                stock_info = STOCK_MAP[stock_name]
                hist_data = get_historical_data(stock_info["code"], 10)  # 最近10天
                
                if not hist_data.empty:
                    with st.expander(f"{stock_name} 最近10个交易日数据"):
                        # 格式化显示
                        display_hist = hist_data.copy()
                        display_hist['pct_change'] = (display_hist['pct_change'] * 100).round(2).astype(str) + "%"
                        display_hist['volume'] = (display_hist['volume'] / 10000).round(1).astype(str) + "万手"
                        display_hist['amount'] = (display_hist['amount'] / 100000000).round(3).astype(str) + "亿"
                        
                        st.dataframe(
                            display_hist[['date', 'open', 'close', 'high', 'low', 
                                         'volume', 'amount', 'pct_change', 'turnover']].rename(columns={
                                'date': '日期',
                                'open': '开盘',
                                'close': '收盘',
                                'high': '最高',
                                'low': '最低',
                                'volume': '成交量',
                                'amount': '成交额',
                                'pct_change': '涨跌幅',
                                'turnover': '换手率'
                            }),
                            use_container_width=True
                        )
        
        # 4. 资金流向
        st.header("💰 资金流向分析")
        
        cols = st.columns(len(selected_stocks))
        for idx, stock_name in enumerate(selected_stocks):
            stock_info = STOCK_MAP[stock_name]
            money_flow = get_money_flow(stock_info["code"])
            
            with cols[idx]:
                st.subheader(stock_name)
                if not money_flow.empty:
                    # 显示最近一天的资金流向
                    latest_flow = money_flow.iloc[0]
                    st.metric("主力净流入", f"{latest_flow.get('主力净流入', 0)/10000:.1f}万元")
                    st.metric("散户净流入", f"{latest_flow.get('散户净流入', 0)/10000:.1f}万元")
                else:
                    st.info("资金流向数据暂时不可用")
    
    else:
        st.warning("无法获取实时行情数据，请稍后重试")
        
else:
    st.info("请在左侧选择要分析的股票")

# 页脚信息
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col2:
    st.caption("数据来源: akshare")
with col3:
    if st.button("🔄 刷新数据"):
        st.cache_data.clear()
        st.rerun()

# 免责声明
st.markdown("""
---
**免责声明**: 本系统数据仅供参考，不构成投资建议。股市有风险，投资需谨慎。
""")