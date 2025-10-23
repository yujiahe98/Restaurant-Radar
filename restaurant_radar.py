import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------
# ✅ Page setup
# ---------------------
st.set_page_config(page_title="Europe Restaurant Dashboard", layout="wide")
st.title("🍽️ Europe Restaurant Data Explorer")
st.markdown("Explore European restaurant data by filtering Cuisine Style, Ratings, and Number of Reviews.")

# ---------------------
# ✅ Data loading
# ---------------------
@st.cache_data
def load_data(path="rest.csv"):
    """Load CSV safely with multiple encoding fallbacks."""
    for enc in ["utf-8", "gbk", "latin1"]:
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Unable to decode CSV file. Please check encoding.")

    # Standardize column names
    df.columns = df.columns.str.strip().str.replace(" ", "_")
    return df

try:
    data = load_data("rest.csv")
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# ---------------------
# ✅ Data cleaning
# ---------------------
# Handle numeric columns
for col in ["Number_of_Reviews", "Rating"]:
    if col in data.columns:
        data[col] = pd.to_numeric(data[col], errors="coerce")

# Handle Cuisine Style
if "Cuisine_Style" not in data.columns:
    st.error("Missing 'Cuisine Style' column in CSV.")
    st.stop()

# Keep only top 10 most common cuisine styles
top10_styles = (
    data["Cuisine_Style"]
    .dropna()
    .astype(str)
    .value_counts()
    .head(10)
    .index
    .tolist()
)
data = data[data["Cuisine_Style"].isin(top10_styles)]

# ---------------------
# ✅ Sidebar filters
# ---------------------
st.sidebar.header("Filter Options")

style_options = top10_styles
selected_style = st.sidebar.multiselect(
    "Select Cuisine Style (Top 10 Most Common)",
    options=style_options,
    default=style_options,
)

st.sidebar.markdown("Filter by Number of Reviews Level:")
views_choice = st.sidebar.radio(
    "Select Range",
    options=["All", "Low (<100)", "Medium (100-499)", "High (>=500)"],
    index=0,
)

min_reviews = int(data["Number_of_Reviews"].min())
max_reviews = int(data["Number_of_Reviews"].max())

reviews_min, reviews_max = st.sidebar.slider(
    "Number of Reviews Range",
    min_value=0,
    max_value=5000,
    value=(min_reviews, max_reviews),
    step=100,
)

st.sidebar.markdown("---")
st.sidebar.write("📊 Total Records:", len(data))

# ---------------------
# ✅ Filtering logic
# ---------------------
df_filtered = data.copy()

if selected_style:
    df_filtered = df_filtered[df_filtered["Cuisine_Style"].isin(selected_style)]
else:
    st.warning("Please select at least one cuisine style.")
    st.stop()

if views_choice == "Low (<100)":
    df_filtered = df_filtered[df_filtered["Number_of_Reviews"] < 100]
elif views_choice == "Medium (100-499)":
    df_filtered = df_filtered[(df_filtered["Number_of_Reviews"] >= 100) & (df_filtered["Number_of_Reviews"] < 500)]
elif views_choice == "High (>=500)":
    df_filtered = df_filtered[df_filtered["Number_of_Reviews"] >= 500]

df_filtered = df_filtered[
    (df_filtered["Number_of_Reviews"] >= reviews_min)
    & (df_filtered["Number_of_Reviews"] <= reviews_max)
]

# ---------------------
# ✅ Line Chart: Reviews vs Ranking
# ---------------------
st.subheader("📈 Ranking by Number of Reviews")

if not df_filtered.empty:
    df_line = df_filtered.sort_values(by="Number_of_Reviews", ascending=False).reset_index(drop=True)
    df_line["Ranking"] = df_line.index + 1

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(
        df_line["Ranking"],
        df_line["Number_of_Reviews"],
        color="#4A72B5",
        linewidth=1.2,
    )
    ax.set_xlabel("Ranking (1 = Most Reviews)", fontsize=11)
    ax.set_ylabel("Number of Reviews", fontsize=11)
    ax.set_title("Ranking by Number of Reviews (Descending)", fontsize=13, weight="bold")
    ax.grid(alpha=0.3)
    st.pyplot(fig)
else:
    st.info("No valid data for line chart.")

# ---------------------
# ✅ Pie Chart: Rating Distribution
# ---------------------
st.subheader("🥧 Average Rating Distribution by Cuisine Style")

if "Rating" in df_filtered.columns and not df_filtered.empty:
    df_filtered = df_filtered.dropna(subset=["Cuisine_Style", "Rating"])
    rating_summary = df_filtered.groupby("Cuisine_Style")["Rating"].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        rating_summary,
        labels=rating_summary.index,
        autopct="%1.1f%%",
        startangle=140,
        textprops={"fontsize": 9},
    )
    ax.set_title("Average Rating by Cuisine Style (Top 10)", fontsize=13, weight="bold")
    ax.axis("equal")
    st.pyplot(fig)
else:
    st.info("No rating data available for the selected cuisine styles.")

# ---------------------
# ✅ Histogram: Review Distribution
# ---------------------
st.subheader("📊 Distribution of Number of Reviews (30 bins)")

fig, ax = plt.subplots(figsize=(8, 5))
if not df_filtered.empty:
    ax.hist(df_filtered["Number_of_Reviews"], bins=30, color="#4A72B5", edgecolor="white", alpha=0.8)
    ax.set_xlabel("Number of Reviews", fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.set_title("Number of Reviews Distribution", fontsize=13, weight="bold")
    ax.grid(alpha=0.3)
    st.pyplot(fig)
else:
    st.info("No data available for histogram.")

# ---------------------
# ✅ Table: Summary + Statistics
# ---------------------
st.subheader("📋 Filtered Dataset Overview")
st.write(f"Number of records after filtering: {len(df_filtered)}")
st.dataframe(df_filtered.head(50))

st.subheader("📐 Key Statistics")
if not df_filtered.empty:
    stats = df_filtered[["Number_of_Reviews"]].agg(["count", "mean", "std", "min", "median", "max"]).T
    stats.columns = ["Count", "Mean", "Std Dev", "Min", "Median", "Max"]
    st.table(stats)
else:
    st.write("No statistics available.")