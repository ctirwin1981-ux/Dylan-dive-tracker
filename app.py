import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Setup
st.set_page_config(page_title="Dylan Irwin Performance Hub", layout="wide")
st.title("🥇 Dylan Irwin - Competitive Diving Performance Tracker")
st.markdown("### *Coach's Analytics Board: Live Google Sheets Sync*")
st.write("---")

# 2. Live Google Sheets Connection
# Using the exact Document ID from your "Dylan Irwin - Competitive Diving Score History" sheet
GOOGLE_SHEET_ID = "1Ytc5af5txVuZYx7wkRYnz9-VQTX9CuDb_IlAJ1OuyXU"
SHEET_NAME = "Dive%20Database"

# This URL tells Google to securely output the specific worksheet as a CSV stream
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# We use st.cache_data so the app doesn't re-download the sheet every time you click a filter!
@st.cache_data(ttl=60) # Refreshes automatically every 60 seconds if data changes
def load_live_data():
    try:
        # Pandas reads the live Google Sheet URL directly
        dataset = pd.read_csv(SHEET_URL)
        return dataset
    except Exception as e:
        st.error(f"Could not connect to the Google Sheet. Please ensure the sharing setting is 'Anyone with the link can view'. Error: {e}")
        return pd.DataFrame()

# Load the data
df = load_live_data()

if not df.empty:
    # Clean up empty rows just in case the Google Sheet has blank lines at the bottom
    df = df.dropna(subset=['Meet', 'Dive Code', 'Points'])
    
    # 3. Code-Driven Data Derivations
    def get_dive_direction(dive_code):
        code_str = str(dive_code).strip()
        if not code_str or code_str == 'nan':
            return "Unknown"
        first_char = code_str[0]
        direction_map = {
            '1': 'Forward', '2': 'Back', '3': 'Reverse', 
            '4': 'Inward', '5': 'Twisting', '6': 'Armstand'
        }
        return direction_map.get(first_char, "Other")

    df['Dive Direction'] = df['Dive Code'].apply(get_dive_direction)
    
    # Calculate Average Judge Execution Score based strictly on the Points and DD formula
    # Formula: (Points / DD) / 3 
    df['Avg Judge Score'] = (pd.to_numeric(df['Points'], errors='coerce') / pd.to_numeric(df['DD'], errors='coerce')) / 3

    # 4. Interactive Sidebar Drill-Down Filters
    st.sidebar.header("🔍 Drill-Down Performance Filters")
    st.sidebar.success("✅ Connected to live Google Sheet")
    
    all_meets = sorted(df['Meet'].dropna().unique())
    selected_meets = st.sidebar.multiselect("Select Meet(s):", options=all_meets, default=all_meets)
    
    all_competitions = sorted(df['Competition'].dropna().unique())
    selected_competitions = st.sidebar.multiselect("Select Competition Group(s):", options=all_competitions, default=all_competitions)
    
    all_directions = sorted(df['Dive Direction'].unique())
    selected_directions = st.sidebar.multiselect("Select Dive Direction(s):", options=all_directions, default=all_directions)
    
    all_dive_names = sorted(df['Dive Name'].dropna().unique())
    selected_dive_names = st.sidebar.multiselect("Select Specific Dive Name(s):", options=all_dive_names, default=all_dive_names)
    
    # Apply filters
    filtered_df = df[
        df['Meet'].isin(selected_meets) &
        df['Competition'].isin(selected_competitions) &
        df['Dive Direction'].isin(selected_directions) &
        df['Dive Name'].isin(selected_dive_names)
    ]
    
    # 5. Dashboard Executive Metrics Summary
    st.subheader("📊 Key Performance Metrics")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="Total Filtered Dives", value=len(filtered_df))
    with kpi2:
        st.metric(label="Highest Dive Points", value=f"{filtered_df['Points'].max():.2f}" if not filtered_df.empty else "0.00")
    with kpi3:
        st.metric(label="Avg Points / Dive", value=f"{filtered_df['Points'].mean():.2f}" if not filtered_df.empty else "0.00")
    with kpi4:
        st.metric(label="Avg Execution Mark (Judges)", value=f"{filtered_df['Avg Judge Score'].mean():.2f}" if not filtered_df.empty else "0.00")
        
    st.write("---")
    
    # 6. Trend Graphs & Visual Analytics
    if not filtered_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Points Progression Timeline")
            trend_df = filtered_df.copy()
            
            fig_trend = px.line(
                trend_df, 
                x='Date', 
                y='Points', 
                hover_data=['Meet', 'Competition', 'Dive Code', 'Dive Name'],
                markers=True,
                title="Points Awarded Mapped by Date",
            )
            fig_trend.update_traces(line_color='#0284c7', marker=dict(size=8))
            st.plotly_chart(fig_trend, use_container_width=True)
            
        with col2:
            st.subheader("🔄 Technical Execution Quality by Direction")
            direction_summary = filtered_df.groupby('Dive Direction')['Avg Judge Score'].mean().reset_index()
            
            fig_bar = px.bar(
                direction_summary, 
                x='Dive Direction', 
                y='Avg Judge Score',
                title="Average Technical Mark per Family",
                color='Dive Direction',
                text_auto='.2f',
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_bar.update_layout(yaxis_range=[0, 10])
            st.plotly_chart(fig_bar, use_container_width=True)
            
        st.write("---")
        
        # 7. Granular Records Log Table
        st.subheader("📋 Filtered Historical Dive Log Rows")
        st.dataframe(
            filtered_df[['Meet', 'Date', 'Competition', 'Dive Code', 'Dive Name', 'DD', 'Avg Judge Score', 'Points', 'Score']],
            use_container_width=True,
            hide_index=True
        )
        
    else:
        st.warning("No data matches your current filter selections. Broaden your sidebar criteria to inspect trends.")
else:
    st.info("Awaiting connection to Google Sheets...")