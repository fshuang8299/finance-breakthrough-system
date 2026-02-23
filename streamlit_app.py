import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime
import plotly.express as px

# 页面设置
st.set_page_config(
    page_title="财务突破系统 V1.0",
    page_icon="💰",
    layout="wide"
)

# 标题
st.title("💰 财务突破系统 V1.0")
st.markdown("---")

# 初始化参数（你可以修改这些）
st.sidebar.header("参数设置")
selected_stocks = st.sidebar.multiselect(
    "选择股票",
    ["000858.SZ", "000568.SZ", "600519.SH"],  # 五粮液, 泸州老窖, 贵州茅台
    default=["000858.SZ", "000568.SZ"]
)

period_days = st.sidebar.slider("分析周期(天)", 30, 365, 90)

# 获取股票数据
@st.cache_data(ttl=300)  # 缓存5分钟
def get_stock_data(stock_code, days):
    try:
        # 使用 ak.stock_zh_a_hist 获取历史数据
        df = ak.stock_zh_a_hist(symbol=stock_code[:6], period="daily", 
                                 start_date=(datetime.now().date() - pd.Timedelta(days=days)).strftime('%Y%m%d'),
                                 end_date=datetime.now().date().strftime('%Y%m%d'))
        df = df[['日期', '开盘', '收盘', '最高', '最低', '成交量']]
        df['股票代码'] = stock_code
        return df
    except Exception as e:
        st.warning(f"获取 {stock_code} 数据失败: {str(e)}")
        return pd.DataFrame()

# 主显示区域
tab1, tab2, tab3 = st.tabs(["📈 实时行情", "📊 持仓监控", "📋 交易记录"])

with tab1:
    st.subheader("实时行情分析")
    
    if selected_stocks:
        # 获取数据
        data_frames = []
        for stock in selected_stocks:
            df = get_stock_data(stock, period_days)
            if not df.empty:
                data_frames.append(df)
        
        if data_frames:
            all_data = pd.concat(data_frames, ignore_index=True)
            
            # 显示数据
            st.dataframe(all_data.tail(10), use_container_width=True)
            
            # 可视化
            st.subheader("股价走势")
            fig = px.line(all_data, x='日期', y='收盘', color='股票代码',
                         title=f"近{period_days}天股价走势")
            st.plotly_chart(fig, use_container_width=True)
            
            # 计算指标
            st.subheader("关键指标")
            col1, col2, col3 = st.columns(3)
            with col1:
                latest_price = all_data.groupby('股票代码')['收盘'].last()
                for code, price in latest_price.items():
                    st.metric(f"{code} 最新价", f"¥{price:.2f}")
            
            with col2:
                avg_volume = all_data.groupby('股票代码')['成交量'].mean()
                for code, vol in avg_volume.items():
                    st.metric(f"{code} 均成交量", f"{vol/10000:.2f}万手")
    else:
        st.info("请在左侧选择股票")

with tab2:
    st.subheader("持仓监控")
    
    # 模拟持仓数据（你可以修改这里）
    holdings = {
        "股票代码": ["000858.SZ", "000568.SZ"],
        "股票名称": ["五粮液", "泸州老窖"],
        "持仓数量": [1000, 800],
        "成本价": [105.00, 117.00],
        "当前价": [105.95, 117.79],  # 实际价格需要从akshare获取
        "持仓市值": [105950, 94232],
        "浮盈/亏(%)": [0.90, 0.68]
    }
    
    holdings_df = pd.DataFrame(holdings)
    st.dataframe(holdings_df, use_container_width=True)
    
    # 计算总资产
    total_value = holdings_df['持仓市值'].sum()
    st.metric("总持仓市值", f"¥{total_value:,.2f}")

with tab3:
    st.subheader("交易记录")
    
    # 模拟交易记录
    trades = {
        "日期": ["2024-01-15", "2024-01-10", "2024-01-05"],
        "操作": ["买入", "买入", "建仓"],
        "股票": ["000858.SZ", "000568.SZ", "000858.SZ"],
        "价格": [105.00, 117.00, 104.50],
        "数量": [500, 800, 500]
    }
    
    trades_df = pd.DataFrame(trades)
    st.dataframe(trades_df, use_container_width=True)

# 页脚
st.markdown("---")
st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("财务突破系统 V1.0 | 实时监控与分析")