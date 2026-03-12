import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import os

# Set page config
st.set_page_config(page_title="Retail Insights Pakistan", layout="wide", page_icon="📈")

# Professional Color Palette & Constants
PRIMARY_COLOR = "#0F172A"  # Slate 900
SECONDARY_COLOR = "#3B82F6" # Blue 500
SUCCESS_COLOR = "#10B981"  # Emerald 500
WARNING_COLOR = "#F59E0B"  # Amber 500
TEXT_MUTED = "#64748B"
BG_LIGHT = "#F8FAFC"

# Design elements & CSS
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .main {{
        background-color: {BG_LIGHT};
        font-family: 'Inter', sans-serif;
    }}
    
    /* Custom Card */
    .metric-card {{
        background: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }}
    
    .metric-label {{
        color: {TEXT_MUTED};
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }}
    
    .metric-value {{
        color: {PRIMARY_COLOR};
        font-size: 1.875rem;
        font-weight: 800;
        margin: 0.25rem 0;
    }}
    
    /* Navigation Bar simulation */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 24px;
        background-color: transparent;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
        color: {TEXT_MUTED};
    }}

    .stTabs [aria-selected="true"] {{
        color: {SECONDARY_COLOR} !important;
        border-bottom: 2px solid {SECONDARY_COLOR} !important;
    }}
    
    /* Product Result Card */
    .product-card {{
        background: white;
        padding: 1.25rem;
        border-radius: 0.5rem;
        border-left: 4px solid {SECONDARY_COLOR};
        margin-bottom: 1rem;
    }}
    
    .cheapest-badge {{
        background-color: {SUCCESS_COLOR};
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
    }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    gold_path = "data/matched/matched_products.jsonl"
    if not os.path.exists(gold_path): return None
    records = []
    with open(gold_path, 'r', encoding='utf-8') as f:
        for line in f: records.append(json.loads(line))
    return records

@st.cache_data
def load_store_metrics():
    path = "reports/store_market_metrics.csv"
    if os.path.exists(path): return pd.read_csv(path)
    return None

def main():
    # Header Area
    col_h1, col_h2 = st.columns([0.8, 0.2])
    with col_h1:
        st.title("🛡️ Retail Intelligence Command")
        st.markdown(f"<p style='color:{TEXT_MUTED}; font-size:1.1rem; margin-top:-15px;'>Market Monitoring & Price Parity Analysis | Pakistan Regions</p>", unsafe_allow_html=True)
    
    data = load_data()
    store_metrics = load_store_metrics()
    
    if not data:
        st.error("Data Hub Offline. Please initialize the Gold Layer pipeline.")
        return

    # Sidebar
    st.sidebar.markdown("### 🛠️ Control Panel")
    cities = list(set([o['city'] for p in data for o in p['offers']]))
    selected_city = st.sidebar.multiselect("Active Regions", cities, default=cities)
    
    categories = sorted(list(set([p['category'] for p in data])))
    selected_cat = st.sidebar.multiselect("Product Verticals", categories, default=categories[:5])

    # Global Stats Row
    total_products = len(data)
    cross_store = sum(1 for p in data if len(p['offers']) > 1)
    avg_spread = sum((p['max_price'] - p['min_price'])/p['min_price'] for p in data if p['min_price'] > 0) / total_products

    st.markdown("---")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Total SKUs</div><div class="metric-value">{total_products:,}</div><div style="color:{SUCCESS_COLOR}; font-size:0.8rem;">↑ 12% vs last sync</div></div>', unsafe_allow_html=True)
    with m_col2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Unique Brands</div><div class="metric-value">{len(set([p["brand"] for p in data])):,}</div><div style="color:{SECONDARY_COLOR}; font-size:0.8rem;">Cross-Store Presence</div></div>', unsafe_allow_html=True)
    with m_col3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Price Match Rate</div><div class="metric-value">{(cross_store/total_products)*100:.1f}%</div><div style="color:{WARNING_COLOR}; font-size:0.8rem;">Matched across stores</div></div>', unsafe_allow_html=True)
    with m_col4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Avg. Price Var</div><div class="metric-value">{avg_spread*100:.1f}%</div><div style="color:{TEXT_MUTED}; font-size:0.8rem;">Market volatility</div></div>', unsafe_allow_html=True)

    # Main Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Market Intelligence", "🏷️ Category Analytics", "🔍 Price Explorer"])

    with tab1:
        c1, c2 = st.columns([1.2, 0.8])
        with c1:
            st.subheader("Leader Dominance Index (LDI)")
            if store_metrics is not None and not store_metrics.empty:
                # Rank stores by LDI (Lower is better)
                fig_ldi = px.bar(store_metrics.sort_values('ldi'), 
                                x='ldi', y='store', orientation='h', color='city',
                                template="plotly_white",
                                color_discrete_sequence=px.colors.qualitative.Prism,
                                title="Pricing Leadership Efficiency")
                fig_ldi.update_layout(showlegend=True, height=450)
                st.plotly_chart(fig_ldi, use_container_width=True)
            else:
                st.info("No market metrics available for the selected view.")
        with c2:
            st.subheader("Competitor Presence")
            store_counts = pd.Series([o['store'] for p in data for o in p['offers']]).value_counts()
            if not store_counts.empty:
                fig_donut = px.pie(values=store_counts.values, names=store_counts.index, hole=.6,
                                template="plotly_white",
                                color_discrete_sequence=[PRIMARY_COLOR, SECONDARY_COLOR, SUCCESS_COLOR])
                fig_donut.update_layout(height=450, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("No competitor data found.")

    with tab2:
        st.subheader("Market Price Distribution")
        cat_df = pd.DataFrame([{
            'category': p['category'], 
            'p': p['min_price'], 
            'city': p['offers'][0]['city']} for p in data if p['category'] in selected_cat])
        
        if not cat_df.empty:
            fig_violin = px.violin(cat_df, y="p", x="category", color="city", box=True, points="all",
                                template="plotly_white", title="Price Density by Retail Vertical")
            st.plotly_chart(fig_violin, use_container_width=True)
            
            # Category Ranking Table
            st.subheader("Category Volatility Ranking")
            vol_df = cat_df.groupby('category')['p'].std().reset_index().rename(columns={'p': 'price_volatility'}).sort_values('price_volatility', ascending=False)
            st.dataframe(vol_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No data found for the selected categories. Please adjust your filters in the sidebar.")

    with tab3:
        search_q = st.text_input("Search Market Database", placeholder="Search for products, brands or sizes...", key="main_search")
        if search_q:
            results = [p for p in data if search_q.lower() in p['title'].lower() or search_q.lower() in p['brand'].lower()]
            if not results:
                st.info("No SKU found for criteria.")
            else:
                for p in results[:15]:
                    with st.container():
                        st.markdown(f"""
                        <div class="product-card">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-weight:800; font-size:1.1rem; color:{PRIMARY_COLOR};">{p['title']}</span>
                                <span style="color:{TEXT_MUTED}; font-size:0.8rem;">ID: {p['product_id'][:8]}</span>
                            </div>
                            <div style="margin-top:5px; font-size:0.9rem;">
                                <b>Brand:</b> {p['brand']} | <b>Category:</b> {p['category']} | <b>Size:</b> {p['quantity']} {p['unit']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Comparison Table & Chart
                        offers = pd.DataFrame(p['offers']).sort_values('price')
                        min_price = offers['price'].min()
                        
                        res_col1, res_col2 = st.columns([0.4, 0.6])
                        with res_col1:
                            for idx, row in offers.iterrows():
                                is_cheapest = row['price'] == min_price
                                badge = f'<span class="cheapest-badge">BEST VALUE</span>' if is_cheapest else ""
                                st.markdown(f"**{row['store']}** ({row['city']}): Rs. {row['price']:,} {badge}", unsafe_allow_html=True)
                        
                        with res_col2:
                            fig_res = px.line(offers, x='store', y='price', markers=True, template="plotly_white")
                            fig_res.update_layout(height=150, margin=dict(t=10, b=10, l=10, r=10), xaxis_title=None, yaxis_title=None)
                            st.plotly_chart(fig_res, use_container_width=True, key=f"chart_{p['product_id']}")
                        st.markdown("<br>", unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown(f"<div style='text-align:center; color:{TEXT_MUTED};'>Retail Intelligence System | Data Source: Metro, Imtiaz, Al-Fatah | Last Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
