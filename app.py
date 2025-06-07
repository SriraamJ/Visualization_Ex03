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

df = load_data()

# Main layout: Two columns
left_col, right_col = st.columns([1, 1])

# Left half: Map and filters
with left_col:
    # World map
    st.markdown("#### Big Mac Prices (USD)")
    selected_date = st.selectbox("", sorted(df['date'].dt.strftime('%Y-%m-%d').unique(), reverse=True), key="date_select")
    filtered_df = df[df['date'].dt.strftime('%Y-%m-%d') == selected_date]
    if not filtered_df.empty:
        fig_map = px.choropleth(filtered_df, locations='iso_a3', color='dollar_price',
                                hover_name='name', hover_data=['dollar_price'],
                                color_continuous_scale=px.colors.sequential.Plasma,
                                labels={'dollar_price': 'Price (USD)'})
        fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), geo=dict(showframe=False, projection_type='equirectangular'), height=350, font=dict(size=10))
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No data for selected date.")

    # Filters
    st.markdown("#### Filters")
    countries = df['name'].unique()
    selected_countries = st.multiselect("", countries, default=["United States", "China", "Euro area"], key="country_select")
    currencies = df['currency_code'].unique()
    selected_currency = st.selectbox("", currencies, index=list(currencies).index('USD'), key="currency_select")

# Filter data for charts
filtered_df = df[df['date'].dt.strftime('%Y-%m-%d') == selected_date]
if selected_countries:
    filtered_df = filtered_df[filtered_df['name'].isin(selected_countries)]

# Right half: Three equal parts
with right_col:
    # Line chart
    st.markdown("#### Price Trend (USD)")
    if selected_countries:
        trend_df = df[df['name'].isin(selected_countries)][['date', 'name', 'dollar_price']]
        fig_trend = px.line(trend_df, x='date', y='dollar_price', color='name',
                            labels={'dollar_price': 'Price (USD)', 'date': 'Date', 'name': 'Country'})
        fig_trend.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=200, font=dict(size=10), showlegend=True)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("Select at least one country.")

    # Bar chart
    st.markdown("#### Raw vs Adjusted USD Price")
    if not filtered_df.empty:
        bar_df = filtered_df[['name', 'USD_raw', 'USD_adjusted']].melt(id_vars='name', 
                                                                       value_vars=['USD_raw', 'USD_adjusted'],
                                                                       var_name='Metric', value_name='Value')
        fig_bar = px.bar(bar_df, x='name', y='Value', color='Metric', barmode='group',
                         labels={'Value': 'Price Index', 'name': 'Country'})
        fig_bar.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=200, font=dict(size=10))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("No data for selected date.")

    # Metrics and insight
    st.markdown("#### Metrics & Insight")
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
        st.markdown(f"**Insight**: Largest raw vs adjusted USD difference in {selected_date}: **{max_diff_country}** ({max_diff:.2f})", unsafe_allow_html=True)
    else:
        st.warning("No data for metrics.")

# Footer
st.markdown("<small>Data: Big Mac Index. Built with Streamlit & Plotly.</small>", unsafe_allow_html=True)