import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px

# 页面设置
st.set_page_config(
    page_title="European Restaurant Explorer",
    page_icon="🍴",
    layout="wide"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #34495e;
    }
    .stat-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


# ...existing code...
@st.cache_data
def load_data():
    from pathlib import Path
    csv_path = Path(__file__).parent / "rest.csv"

    if not csv_path.exists():
        st.error(f"rest.csv not found at: {csv_path}")
        st.stop()

    encodings = ["utf-8", "utf-8-sig", "gbk", "gb18030", "latin1"]
    df = None
    last_err = None
    for enc in encodings:
        try:
            # 读取时去掉开头的 unnamed 索引列
            df = pd.read_csv(csv_path, encoding=enc, low_memory=False, index_col=0)
            used_enc = enc
            break
        except Exception as e:
            last_err = e

    if df is None:
        # 最后回退尝试（更宽容）
        try:
            df = pd.read_csv(csv_path, encoding="latin1", engine="python", low_memory=False, index_col=0, on_bad_lines="warn")
            used_enc = "latin1-fallback"
        except Exception as e:
            st.error(f"无法读取 rest.csv。最后一次尝试错误：{last_err}; 回退错误：{e}")
            st.write("请确认文件路径和文件编码，或把终端/浏览器中的完整 traceback 贴给我。")
            st.stop()

    st.info(f"Loaded rest.csv using encoding: {used_enc}")

    # 清理列名与字符串字段两端空白
    df.columns = df.columns.str.strip()
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].str.strip()

    # 必要列检查（修正 Price Range 拼写）
    required_columns = [
        'Name', 'City', 'Cuisine Style', 'Ranking',
        'Rating', 'Price Range', 'Number of Reviews',
    ]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"Missing columns in rest.csv: {', '.join(missing_cols)}")
        st.write("CSV header preview:")
        st.write(df.head(3))
        st.stop()

    # 确保评论数为数值
    if 'Number of Reviews' in df.columns:
        df['Number of Reviews'] = pd.to_numeric(df['Number of Reviews'], errors='coerce').fillna(0).astype(int)

    # 将 Rating 转为数值，避免 UI 控件报错
    if 'Rating' in df.columns:
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
        # 如果全是 NaN，填 0；否则用列最小值填充缺失（避免 slider 的 min/max 出错）
        if pd.isna(df['Rating'].min()):
            df['Rating'] = df['Rating'].fillna(0)
        else:
            df['Rating'] = df['Rating'].fillna(df['Rating'].min())

    if 'review_volume' not in df.columns:
        df['review_volume'] = pd.cut(
            df['Number of Reviews'].fillna(0).astype(int),
            bins=[-1, 1000, 3000, np.inf],
            labels=['Low', 'Medium', 'High']
        )

    df = df.rename(columns={
        'Name': 'restaurant_name',
        'City': 'city',
        'Cuisine Style': 'cuisine',
        'Rating': 'rating',
        'Price Range': 'price_range',
        'Number of Reviews': 'review_count'
    })

    return df
# ...existing code...



# 加载数据
df = load_data()
original_df = df.copy()


# --------------------------
# 2. 顶部筛选区（匹配你的数据列）
# --------------------------
st.markdown('<h1 class="main-header">🍴 European Restaurant Explorer</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Discover restaurants with interactive filters</p>', unsafe_allow_html=True)

# 筛选组件
col1, col2, col3 = st.columns(3)

with col1:
    selected_cities = st.multiselect(
        "Cities",
        options=df['city'].unique(),
        default=df['city'].unique(),
        placeholder="Select cities..."
    )

with col2:
    selected_cuisines = st.multiselect(
        "Cuisine Styles",
        options=df['cuisine'].unique(),
        default=df['cuisine'].unique(),
        placeholder="Select cuisines..."
    )

with col3:
    price_ranges = st.multiselect(
        "Price Ranges",
        options=df['price_range'].unique(),
        default=df['price_range'].unique(),
        placeholder="Select price ranges..."
    )

# 额外筛选条件
col4, col5 = st.columns(2)

with col4:
    min_rating = st.slider(
        "Minimum Rating",
        min_value=float(df['rating'].min()),
        max_value=float(df['rating'].max()),
        value=float(df['rating'].min()),
        step=0.1
    )

with col5:
    review_volume = st.radio(
        "Review Volume",
        options=['All', 'Low', 'Medium', 'High'],
        horizontal=True
    )


# --------------------------
# 3. 数据筛选逻辑
# --------------------------
filtered_df = df[
    (df['city'].isin(selected_cities)) &
    (df['cuisine'].isin(selected_cuisines)) &
    (df['price_range'].isin(price_ranges)) &
    (df['rating'] >= min_rating)
]

if review_volume != 'All':
    filtered_df = filtered_df[filtered_df['review_volume'] == review_volume]


# --------------------------
# 4. 数据统计卡片
# --------------------------
st.subheader("📊 Key Statistics")
stat1, stat2, stat3, stat4 = st.columns(4)

with stat1:
    st.markdown('<div class="stat-card">', unsafe_allow_html=True)
    st.metric("Total Restaurants", len(filtered_df))
    st.markdown('</div>', unsafe_allow_html=True)

with stat2:
    st.markdown('<div class="stat-card">', unsafe_allow_html=True)
    st.metric("Avg. Rating", round(filtered_df['rating'].mean(), 1) if not filtered_df.empty else 0)
    st.markdown('</div>', unsafe_allow_html=True)

with stat3:
    st.markdown('<div class="stat-card">', unsafe_allow_html=True)
    st.metric("Total Reviews", filtered_df['review_count'].sum() if not filtered_df.empty else 0)
    st.markdown('</div>', unsafe_allow_html=True)

with stat4:
    st.markdown('<div class="stat-card">', unsafe_allow_html=True)
    st.metric("Cuisine Types", filtered_df['cuisine'].nunique() if not filtered_df.empty else 0)
    st.markdown('</div>', unsafe_allow_html=True)


# --------------------------
# 5. 数据表格展示（匹配你的列）
# --------------------------
st.subheader("🍽️ Restaurant List")
st.dataframe(
    filtered_df[
        ['restaurant_name', 'city', 'cuisine', 'rating', 
         'review_count', 'price_range', 'Ranking']  # 包含你的Ranking列
    ],
    hide_index=True,
    use_container_width=True,
    column_config={
        'rating': st.column_config.NumberColumn(format="%.1f ⭐"),
        'review_count': st.column_config.NumberColumn(format="%d reviews"),
        'Ranking': st.column_config.NumberColumn(format="%d")
    }
)

# 下载功能
st.download_button(
    "💾 Download Filtered Data",
    data=filtered_df.to_csv(index=False),
    file_name="european_restaurants_filtered.csv",
    mime="text/csv"
)


# --------------------------
# 6. 可视化区域（适配你的数据）
# --------------------------
st.subheader("📈 Data Visualizations")

# 图表1：如果有经纬度则显示地图，否则显示城市分布
if 'latitude' in df.columns and 'longitude' in df.columns and not filtered_df.empty:
    fig1 = px.scatter_mapbox(
        filtered_df,
        lat="latitude",
        lon="longitude",
        hover_name="restaurant_name",
        hover_data=["cuisine", "rating", "price_range"],
        color="cuisine",
        zoom=4,
        mapbox_style="carto-positron",
        title="Restaurant Locations by Cuisine",
        height=500
    )
    st.plotly_chart(fig1, use_container_width=True)
else:
    # 无经纬度时显示城市餐厅数量柱状图
    if not filtered_df.empty:
        city_counts = filtered_df['city'].value_counts().reset_index()
        city_counts.columns = ['city', 'count']
        fig1 = px.bar(
            city_counts,
            x='city',
            y='count',
            color='city',
            text_auto=True,
            title="Restaurants per City",
            height=500
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

# 图表2和3：并排展示
col6, col7 = st.columns(2)

with col6:
    if not filtered_df.empty:
        # 各菜系平均评分
        cuisine_rating = filtered_df.groupby('cuisine')['rating'].mean().sort_values(ascending=False).reset_index()
        fig2 = px.bar(
            cuisine_rating,
            x='cuisine',
            y='rating',
            color='cuisine',
            text_auto=".1f",
            title="Average Rating by Cuisine",
            height=400
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

with col7:
    if not filtered_df.empty:
        # 评分分布直方图
        fig3 = px.histogram(
            filtered_df,
            x='rating',
            nbins=10,
            color_discrete_sequence=['#3498db'],
            title="Rating Distribution",
            height=400
        )
        fig3.update_xaxes(title_text="Rating")
        fig3.update_yaxes(title_text="Number of Restaurants")
        st.plotly_chart(fig3, use_container_width=True)