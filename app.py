import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="Big Mac Index Dashboard", layout="wide")

# Load and clean data
@st.cache_data
def load_data():
    df = pd.read_csv('big-mac-full-index-cleaned.csv')
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    numeric_cols = ['local_price', 'dollar_ex', 'dollar_price', 'USD_raw', 'EUR_raw', 
                    'GBP_raw', 'JPY_raw', 'CNY_raw', 'GDP_bigmac', 'adj_price', 
                    'USD_adjusted', 'EUR_adjusted', 'GBP_adjusted', 'JPY_adjusted', 'CNY_adjusted']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['date', 'iso_a3', 'name', 'dollar_price'])
    return df

df_ppp = pd.read_csv('ppp.csv')

df = load_data()
df['year'] = df['date'].dt.year
df_ppp = df_ppp.rename(columns={'Country': 'name', 'Year': 'year'})  # Rename columns to match
merged_df = pd.merge(
    df,
    df_ppp,
    on=['name', 'year'],  # or whatever your column names are
    how='left'  # keeps all rows from your main dataset
)

# Main layout: Two columns
left_col, right_col = st.columns([1, 1])

# Left half: Map and filters
with left_col:
    # World map
    st.markdown("#### Big Mac Index (USD)")
    selected_date = st.selectbox("", sorted(df['date'].dt.strftime('%Y-%m-%d').unique(), reverse=True), key="date_select")
    filtered_df = df[df['date'].dt.strftime('%Y-%m-%d') == selected_date]
    filtered_df['dollar_price'] = filtered_df['dollar_price'].round(2)
    filtered_df['local_price'] = filtered_df['local_price'].round(2)
    if not filtered_df.empty:
        fig_map = px.choropleth(filtered_df, locations='iso_a3', color='USD_adjusted',
                                hover_name='name', hover_data=['dollar_price', 'local_price'],
                                color_continuous_scale=px.colors.sequential.Plasma_r,
                                labels={'dollar_price': 'Price (USD)', 'local_price': 'Price (Local Currency)', 'iso_a3': 'Code', 'USD_adjusted': "BMI (Adjusted)"},)
        fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), geo=dict(showframe=False, projection_type='equirectangular'), height=350, font=dict(size=10))
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No data for selected date.")

    st.markdown("#### Raw Data Table")
    columns_to_show = ["name", "iso_a3", "year", "dollar_price", "USD_raw", "USD_adjusted", "GDP_bigmac", "PPP"]

    # Display the table
    st.dataframe(merged_df[columns_to_show].rename(columns={"iso_a3": "code", "dollar_price": "price", "USD_raw": "bmi_raw", "USD_adjusted": "bmi_adjusted", "GDP_bigmac": "gdp_per_capita", "PPP": "ppp"}))

# Right half
with right_col:
    # Filters
    st.markdown("#### Country Selection")
    countries = df['name'].unique()
    selected_countries = st.multiselect("", countries, default=["United States", "China", "Switzerland"], key="country_select")

    # Filter data for charts
    filtered_df = df[df['date'].dt.strftime('%Y-%m-%d') == selected_date]
    if selected_countries:
        filtered_df = filtered_df[filtered_df['name'].isin(selected_countries)]


    # Line chart
    st.markdown("#### Big Mac Price (USD)")
    if selected_countries:
        trend_df = df[df['name'].isin(selected_countries)][['date', 'name', 'dollar_price']]
        fig_trend = px.line(trend_df, x='date', y='dollar_price', color='name',
                            labels={'dollar_price': 'Price (USD)', 'date': 'Date', 'name': 'Country'})
        fig_trend.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=200, font=dict(size=10), showlegend=True)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("Select at least one country.")

    st.markdown("#### GDP/Capita (USD)")
    if selected_countries:
        trend_df = df[df['name'].isin(selected_countries)][['date', 'name', 'GDP_bigmac']]
        fig_trend = px.line(trend_df, x='date', y='GDP_bigmac', color='name',
                            labels={'GDP_bigmac': 'GDP/c (USD)', 'date': 'Date', 'name': 'Country'})
        fig_trend.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=200, font=dict(size=10), showlegend=True)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("Select at least one country.")

    st.markdown("#### Purchasing Power Parity Conversion Factor (USD)")
    if selected_countries:
        trend_df = merged_df[merged_df['name'].isin(selected_countries)][['date', 'name', 'PPP']]
        fig_trend = px.line(trend_df, x='date', y='PPP', color='name',
                            labels={'PPP': 'ppp', 'date': 'Date', 'name': 'Country'})
        fig_trend.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=200, font=dict(size=10), showlegend=True)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("Select at least one country.")



    # Metrics and insight
    st.markdown("#### Metrics")
    if not filtered_df.empty:
        col1, col2, col3 = st.columns(3)
        avg_price = filtered_df['dollar_price'].mean()
        avg_gdp = filtered_df['GDP_bigmac'].mean()
        most_expensive = filtered_df.loc[filtered_df['dollar_price'].idxmax(), 'name']
        most_expensive_price = filtered_df['dollar_price'].max()
        with col1:
            st.markdown(f"**Avg Price (USD)**<br>${avg_price:.2f}", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**Avg GDP/Capita**<br>${avg_gdp:,.0f}", unsafe_allow_html=True)
        with col3:
            st.markdown(f"**Most Expensive**<br>{most_expensive} (${most_expensive_price:.2f})", unsafe_allow_html=True)
        max_diff_country = filtered_df.loc[abs(filtered_df['USD_adjusted'] - filtered_df['USD_raw']).idxmax(), 'name']
        max_diff = abs(filtered_df['USD_adjusted'] - filtered_df['USD_raw']).max()
    else:
        st.warning("No data for metrics.")

# Footer
st.markdown("<small>Data: [The Economist’s Big Mac index](https://github.com/TheEconomist/big-mac-data/tree/2025-01); [PPP conversion factor, GDP (LCU per international $). World Bank, International Comparison Program database](https://data.worldbank.org/indicator/PA.NUS.PPP). Built with Streamlit & Plotly.</small>", unsafe_allow_html=True)