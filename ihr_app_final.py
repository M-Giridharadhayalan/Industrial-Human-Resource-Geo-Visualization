import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(page_title="Industrial HR Dashboard", layout="wide")
st.title("🏭 Industrial HR Analytics Dashboard")

# Load and process data
# Load and process data
def load_data():
    st.sidebar.header("📁 Upload CSV File")
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=['csv'])

    if uploaded_file:
        try:
            # Try default comma delimiter first
            try:
                df = pd.read_csv(uploaded_file)
            except:
                # Fallback to tab delimiter if comma fails
                df = pd.read_csv(uploaded_file, delimiter='\t')

            df.columns = df.columns.str.strip()  # Clean column names
            st.sidebar.success(f"✅ Loaded: {df.shape[0]} rows, {df.shape[1]} columns")
            return process_data(df)
        except Exception as e:
            st.sidebar.error(f"❌ Error loading file: {e}")
            return pd.DataFrame()

    st.sidebar.info("📤 Upload a CSV file to begin analysis")
    return pd.DataFrame()

@st.cache_data
def process_data(df):
    required_cols = [
        'NIC_Name', 'Main_Workers_Total_Persons', 'Marginal_Workers_Total_Persons',
        'Main_Workers_Total_Females', 'Marginal_Workers_Total_Females',
        'Main_Workers_Urban_Persons', 'Marginal_Workers_Urban_Persons',
        'Main_Workers_Rural_Persons', 'Marginal_Workers_Rural_Persons',
        'Main_Workers_Total_Males', 'Marginal_Workers_Total_Males'
    ]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"Missing columns: {', '.join(missing)}")
        return pd.DataFrame()

    for col in required_cols[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['Total Workers'] = df['Main_Workers_Total_Persons'] + df['Marginal_Workers_Total_Persons']
    df['Female Ratio'] = (df['Main_Workers_Total_Females'] + df['Marginal_Workers_Total_Females']) / df['Total Workers']
    df['Urban Ratio'] = (df['Main_Workers_Urban_Persons'] + df['Marginal_Workers_Urban_Persons']) / df['Total Workers']
    df['Female Ratio'] = df['Female Ratio'].replace([np.inf, -np.inf], 0).fillna(0)
    df['Urban Ratio'] = df['Urban Ratio'].replace([np.inf, -np.inf], 0).fillna(0)

    def classify_industry(name):
        if not isinstance(name, str): return 'Other'
        name = name.lower()
        if any(x in name for x in ['crop', 'animal', 'farm', 'agriculture']): return 'Agriculture'
        if any(x in name for x in ['manufactur', 'factory', 'production']): return 'Manufacturing'
        if any(x in name for x in ['retail', 'trade', 'shop']): return 'Retail & Trade'
        if any(x in name for x in ['poultry', 'cattle', 'livestock']): return 'Poultry & Livestock'
        if any(x in name for x in ['mining', 'quarry', 'coal']): return 'Mining'
        return 'Other'

    df['Industry Category'] = df['NIC_Name'].apply(classify_industry)
    return df

def generate_insights(df):
    insights = {}
    industry_share = df.groupby('Industry Category')['Total Workers'].sum()
    total = industry_share.sum()
    insights['top_industry'] = industry_share.idxmax()
    insights['top_share'] = (industry_share.max() / total * 100)

    female_total = (df['Main_Workers_Total_Females'] + df['Marginal_Workers_Total_Females']).sum()
    insights['female_percent'] = (female_total / df['Total Workers'].sum() * 100)

    marginal_total = df['Marginal_Workers_Total_Persons'].sum()
    insights['marginal_percent'] = (marginal_total / df['Total Workers'].sum() * 100)

    industry_stats = df.groupby('Industry Category').agg({
        'Total Workers': 'sum', 'Female Ratio': 'mean', 'Urban Ratio': 'mean'
    })
    industry_stats['Growth Score'] = (industry_stats['Urban Ratio'] * 0.4 + industry_stats['Female Ratio'] * 0.6)
    insights['growth_industry'] = industry_stats['Growth Score'].idxmax()

    return insights

# Visualization functions
def plot_industry_distribution(df):
    industry_totals = df.groupby('Industry Category')['Total Workers'].sum().sort_values(ascending=False)
    fig = px.bar(industry_totals.head(10), orientation='h',
                 title="Top 10 Industries by Total Workers",
                 labels={'value': 'Total Workers', 'index': 'Industry'})
    st.plotly_chart(fig, use_container_width=True)

def plot_gender_analysis(df):
    male_total = (df['Main_Workers_Total_Males'] + df['Marginal_Workers_Total_Males']).sum()
    female_total = (df['Main_Workers_Total_Females'] + df['Marginal_Workers_Total_Females']).sum()
    fig = px.pie(values=[male_total, female_total], names=['Male', 'Female'],
                 title="Overall Gender Composition")
    st.plotly_chart(fig, use_container_width=True)

def plot_urban_rural(df):
    rural = (df['Main_Workers_Rural_Persons'] + df['Marginal_Workers_Rural_Persons']).sum()
    urban = (df['Main_Workers_Urban_Persons'] + df['Marginal_Workers_Urban_Persons']).sum()
    fig = px.pie(values=[rural, urban], names=['Rural', 'Urban'],
                 title="Rural vs Urban Workforce")
    st.plotly_chart(fig, use_container_width=True)

def plot_growth_potential(df):
    industry_stats = df.groupby('Industry Category').agg({
        'Total Workers': 'sum', 'Female Ratio': 'mean', 'Urban Ratio': 'mean'
    })
    industry_stats['Growth Score'] = (industry_stats['Urban Ratio'] * 0.4 + industry_stats['Female Ratio'] * 0.6)
    top_growth = industry_stats.nlargest(8, 'Growth Score')

    fig = go.Figure()
    fig.add_trace(go.Bar(name='Urban Ratio', x=top_growth.index, y=top_growth['Urban Ratio']))
    fig.add_trace(go.Bar(name='Female Ratio', x=top_growth.index, y=top_growth['Female Ratio']))
    fig.update_layout(title="Top Industries by Growth Potential", barmode='group')
    st.plotly_chart(fig, use_container_width=True)

# Main app
def main():
    df = load_data()
    if df.empty:
        st.info("📤 Upload your industrial workforce Excel file to begin analysis.")
        return

    st.sidebar.subheader("📊 Summary")
    st.sidebar.metric("Total Workforce", f"{df['Total Workers'].sum():,}")
    st.sidebar.metric("Industries", df['NIC_Name'].nunique())
    st.sidebar.metric("Categories", df['Industry Category'].nunique())

    insights = generate_insights(df)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Workers", f"{df['Total Workers'].sum():,}")
    with col2: st.metric("Female Workforce", f"{insights['female_percent']:.1f}%")
    with col3: st.metric("Marginal Workers", f"{insights['marginal_percent']:.1f}%")
    with col4: st.metric("Top Industry", insights['top_industry'])

    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🏭 Industries", "🔍 Insights", "📊 Charts"])

    with tab1:
        st.subheader("Workforce Overview")
        col1, col2 = st.columns(2)
        with col1: plot_industry_distribution(df)
        with col2: plot_gender_analysis(df)
        col3, col4 = st.columns(2)
        with col3: plot_urban_rural(df)
        with col4: plot_growth_potential(df)

    with tab2:
        st.subheader("Industry Analysis")
        top_industries = df.groupby('NIC_Name').agg({
            'Total Workers': 'sum',
            'Female Ratio': 'mean',
            'Urban Ratio': 'mean'
        }).nlargest(15, 'Total Workers')
        st.dataframe(top_industries.style.format({
            'Total Workers': '{:,}',
            'Female Ratio': '{:.2%}',
            'Urban Ratio': '{:.2%}'
        }))

    with tab3:
        st.subheader("Strategic Insights")

        st.info(f"🏆 Dominant Sector: **{insights['top_industry']}** employs **{insights['top_share']:.1f}%** of the total workforce")

        st.warning(f"⚠️ Workforce Vulnerability: **{insights['marginal_percent']:.1f}%** are marginal workers needing social security")

        st.success(f"🚀 Growth Opportunity: **{insights['growth_industry']}** shows highest growth potential based on urbanization and gender inclusion")

        st.error(f"👥 Gender Gap: Only **{insights['female_percent']:.1f}%** female participation — opportunity to improve gender equity")

        st.subheader("🎯 Recommendations")
        st.markdown(f"""
        1. **Invest in `{insights['growth_industry']}`** – High potential for inclusive job creation  
        2. **Formalize `{insights['top_industry']}`** – Largest employer needs stability and regulation  
        3. **Gender Programs** – Bridge the **{100 - insights['female_percent']:.1f}%** gender gap through targeted skilling and inclusion  
        4. **Social Security Measures** – Protect **{insights['marginal_percent']:.1f}%** marginal workers with benefits and formal contracts  
        """)

    with tab4:
        st.subheader("Interactive Charts")

        # Gender distribution by industry
        industry_comparison = df.groupby('Industry Category').agg({
            'Total Workers': 'sum',
            'Main_Workers_Total_Males': 'sum',
            'Main_Workers_Total_Females': 'sum'
        }).nlargest(10, 'Total Workers')

        fig = px.bar(industry_comparison,
                     y=industry_comparison.index,
                     x=['Main_Workers_Total_Males', 'Main_Workers_Total_Females'],
                     orientation='h',
                     title="Gender Distribution by Industry",
                     barmode='stack',
                     labels={'value': 'Workers', 'variable': 'Gender'})
        st.plotly_chart(fig, use_container_width=True)

        # Scatter plot: Urbanization vs Female Ratio
        scatter_data = df.groupby('Industry Category').agg({
            'Urban Ratio': 'mean',
            'Female Ratio': 'mean',
            'Total Workers': 'sum'
        })

        fig = px.scatter(scatter_data, x='Urban Ratio', y='Female Ratio',
                         size='Total Workers', color=scatter_data.index,
                         title="Urbanization vs Gender Diversity",
                         hover_name=scatter_data.index)
        st.plotly_chart(fig, use_container_width=True)

    # Raw data viewer
    with st.expander("📋 View Raw Data"):
        st.dataframe(df.head(100))

if __name__ == "__main__":
    main()