import streamlit as st
import pandas as pd
import plotly.express as px
import re


#  Load and Clean Data

@st.cache_data
def load_data():
    df = pd.read_csv(".venv\ihr_geo_data.csv")
    df.columns = [re.sub(r"[^a-zA-Z0-9_]", "", c.replace(" ", "_")) for c in df.columns]
    return df

df = load_data()


# NLP-Based Business Category Classification

keywords = {
    "Retail": ["retail", "trade"],
    "Poultry": ["poultry", "chicken"],
    "Agriculture": ["crop", "agriculture", "farming", "plant", "animal", "forestry", "aquaculture", "fish", "hunting"],
    "Manufacturing": ["manufacturing", "fabrication", "production", "assembly", "processing"],
    "Mining": ["mining", "quarrying", "extraction", "petroleum", "coal", "ore", "logging"],
}

def assign_category(nic):
    t = str(nic).lower()
    for k, kws in keywords.items():
        if any(kw in t for kw in kws):
            return k
    return "Other"

if "Business_Category" not in df.columns:
    df["Business_Category"] = df["NIC_Name"].apply(assign_category)


# Auto-detect Key Columns

geo_col = next((col for col in df.columns if "Division" in col or "State" in col), "Division")
industry_col = "Business_Category"
workers_col = next((col for col in df.columns if "Main_Workers" in col and "Total" in col and "Persons" in col), None)

if not workers_col:
    st.error("Could not detect a valid worker count column. Please check your dataset.")
    st.stop()


# Sidebar Filters

st.sidebar.title("Filters")
geos = sorted(df[geo_col].dropna().unique())
industries = sorted(df[industry_col].dropna().unique())

selected_geos = st.sidebar.multiselect("Select Geographies", geos, default=geos)
selected_inds = st.sidebar.multiselect("Select Industries", industries, default=industries)


# Filtered Data

filtered = df[df[geo_col].isin(selected_geos) & df[industry_col].isin(selected_inds)]


# Aggregated View

agg = filtered.groupby([geo_col, industry_col])[workers_col].sum().reset_index()


# Dashboard Layout

st.title("🧠 Industry Workforce Dashboard")

st.header("📊 Workers by Industry and Geography")
fig = px.bar(
    agg,
    x=geo_col,
    y=workers_col,
    color=industry_col,
    barmode="group",
    labels={workers_col: "Worker Count"},
    title="Workforce Distribution by Region and Sector"
)
st.plotly_chart(fig, use_container_width=True)


# Key Business Insights

st.header("📌 Facts & Figures")
st.write(f"**Regions included:** {', '.join(selected_geos)}")
st.write(f"**Business categories:** {', '.join(selected_inds)}")

st.metric("Total Workers", int(agg[workers_col].sum()))
top_ind = agg.groupby(industry_col)[workers_col].sum().idxmax()
st.metric("Largest Employment Sector", top_ind)
top_geo = agg.groupby(geo_col)[workers_col].sum().idxmax()
st.metric("Top Geography by Workforce", top_geo)


# Pie Chart: Sectoral Share

st.subheader("📈 Sectoral Worker Distribution")
pie_data = agg.groupby(industry_col)[workers_col].sum().reset_index()
fig2 = px.pie(pie_data, names=industry_col, values=workers_col, title="Share by Sector")
st.plotly_chart(fig2, use_container_width=True)


# Optional: Download Filtered Data

st.download_button("📥 Download Filtered Data", filtered.to_csv(index=False), "filtered_data.csv")
