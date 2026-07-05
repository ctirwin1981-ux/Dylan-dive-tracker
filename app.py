import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Mobile-First Page Configurations
st.set_page_config(
    page_title="Dylan Irwin Hub", 
    layout="centered",  # Centered layout feels like a native mobile app scroll
    initial_sidebar_state="collapsed"  # Keeps filters tucked away on small screens
)

st.title("🥇 Dylan Irwin Analytics")
st.caption("Coach's Mobile Performance Board")
st.write("---")

# 2. Live Google Sheets Data Stream
GOOGLE_SHEET_ID = "1Ytc5af5txVuZYx7wkRYnz9-VQTX9CuDb_IlAJ1OuyXU"
SHEET_NAME = "Dive%20Database"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=30)
def load_live_data():
    try:
        return pd.read_csv(SHEET_URL)
    except Exception as e:
        st.error("Sheet Connection Error")
        return pd.DataFrame()

df = load_live_data()

if not df.empty:
    df = df.dropna(subset=['Meet', 'Dive Code', 'Points'])
    
    # --- AUTOMATIC AGE GROUP EXTRACTION ---
    def extract_age_group(comp_name):
        comp_str = str(comp_name).upper()
        # Checks for standard references like 'GROUP A', 'GROUP B', 'OPEN A', 'OPEN B'
        for letter in ['A', 'B', 'C', 'D']:
            if f"GROUP {letter}" in comp_str or f"OPEN {letter}" in comp_str:
                return f"Age Group {letter}"
        return "Other / Open"

    df['Age Group'] = df['Competition'].apply(extract_age_group)

    # --- OTHER DATA DERIVATIONS ---
    def get_dive_direction(dive_code):
        code_str = str(dive_code).strip()
        if not code_str or code_str == 'nan': return "Unknown"
        direction_map = {'1': 'Forward', '2': 'Back', '3': 'Reverse', '4': 'Inward', '5': 'Twisting', '6': 'Armstand'}
        return direction_map.get(code_str[0], "Other")

    df['Dive Direction'] = df['Dive Code'].apply(get_dive_direction)
    df['Avg Judge Score'] = (pd.to_numeric(df['Points'], errors='coerce') / pd.to_numeric(df['DD'], errors='coerce')) / 3

    # --- MOBILE OPTIMIZED FILTER ACCORDION ---
    # On a phone, sidebars can be clunky. An expander container at the top is much cleaner.
    with st.expander("🔍 Tap to Filter & Drill-Down", expanded=False):
        all_ages = sorted(df['Age Group'].unique())
        selected_ages = st.multiselect("Age Group:", options=all_ages, default=all_ages)
        
        # Dynamically filter the subsequent dropdown options based on selected age groups
        temp_df = df[df['Age Group'].isin(selected_ages)]
        
        all_meets = sorted(temp_df['Meet'].dropna().unique())
        selected_meets = st.multiselect("Meet Split:", options=all_meets, default=all_meets)
        
        temp_df = temp_df[temp_df['Meet'].isin(selected_meets)]
        
        all_directions = sorted(temp_df['Dive Direction'].unique())
        selected_directions = st.multiselect("Dive Direction:", options=all_directions, default=all_directions)
        
        all_dive_names = sorted(temp_df['Dive Name'].dropna().unique())
        selected_dive_names = st.multiselect("Specific Dive:", options=all_dive_names, default=all_dive_names)

    # Apply Master Filters
    filtered_df = df[
        df['Age Group'].isin(selected_ages) &
        df['Meet'].isin(selected_meets) &
        df['Dive Direction'].isin(selected_directions) &
        df['Dive Name'].isin(selected_dive_names)
    ]
    
    # --- MOBILE COMPACT KPI TILES ---
    # Stacking KPIs vertically or in pairs avoids text clipping on narrow viewports
    kpi_col1, kpi_col2 = st.columns(2)
    with kpi_col1:
        st.metric(label="Dives Logged", value=len(filtered_df))
        st.metric(label="Avg Points", value=f"{filtered_df['Points'].mean():.2f}" if not filtered_df.empty else "0.00")
    with kpi_col2:
        st.metric(label="Top Dive Points", value=f"{filtered_df['Points'].max():.2f}" if not filtered_df.empty else "0.00")
        st.metric(label="Avg Technical Execution", value=f"{filtered_df['Avg Judge Score'].mean():.2f}" if not filtered_df.empty else "0.00")
        
    st.write("---")
    
    # --- MOBILE SCALED CHART VERTICAL STACK ---
    if not filtered_df.empty:
        st.markdown("#### 📈 Points Progression")
        fig_trend = px.line(
            filtered_df, x='Date', y='Points', 
            hover_data=['Meet', 'Dive Code'], markers=True
        )
        fig_trend.update_traces(line_color='#0284c7', marker=dict(size=7))
        # Reduce margins so the chart stretches cleanly edge-to-edge on phone viewports
        fig_trend.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260)
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
        
        st.write("---")
        
        st.markdown("#### 🔄 Technical Execution by Family")
        direction_summary = filtered_df.groupby('Dive Direction')['Avg Judge Score'].mean().reset_index()
        fig_bar = px.bar(
            direction_summary, x='Dive Direction', y='Avg Judge Score',
            text_auto='.2f', color='Dive Direction',
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_bar.update_layout(yaxis_range=[0, 10], margin=dict(l=10, r=10, t=10, b=10), height=260, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        
        st.write("---")
        
        # --- TOUCH-FRIENDLY LOG DATAFRAME ---
        st.markdown("#### 📋 Filtered Dive Log")
        # Streamlit's native interactive dataframe handles touch swipe scrolling automatically
        st.dataframe(
            filtered_df[['Meet', 'Date', 'Age Group', 'Dive Code', 'DD', 'Avg Judge Score', 'Points']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("Adjust your drop filters above to show performance trends.")