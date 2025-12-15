# Air Tracker: Flight Analytics - Streamlit Application
# Purpose: Interactive dashboard for flight analytics and airport insights

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Air Tracker - Flight Analytics",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .header-title {
        font-size: 2.5em;
        font-weight: bold;
        color: #1f77b4;
    }
    .subheader {
        font-size: 1.5em;
        color: #2c3e50;
        margin-top: 30px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Database Connection
# ============================================================================

@st.cache_resource
def get_db_connection():
    """Create and cache database connection"""
    try:
        conn = sqlite3.connect('flight_analytics.db')
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

# ============================================================================
# Query Execution Functions
# ============================================================================

def execute_query(query: str) -> pd.DataFrame:
    """Execute SQL query and return results as DataFrame"""
    try:
        conn = get_db_connection()
        if conn:
            df = pd.read_sql_query(query, conn)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Query execution error: {e}")
        return pd.DataFrame()

# ============================================================================
# Dashboard Functions
# ============================================================================

def show_home_dashboard():
    """Display homepage with summary statistics"""
    st.markdown("<div class='header-title'>✈️ Air Tracker: Flight Analytics Dashboard</div>", 
                unsafe_allow_html=True)
    st.markdown("---")
    
    # Summary Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        query = "SELECT COUNT(*) as count FROM airport"
        result = execute_query(query)
        count = result['count'].values[0] if not result.empty else 0
        st.metric("Total Airports", count, delta=None)
    
    with col2:
        query = "SELECT COUNT(*) as count FROM flights"
        result = execute_query(query)
        count = result['count'].values[0] if not result.empty else 0
        st.metric("Total Flights", count, delta=None)
    
    with col3:
        query = "SELECT COUNT(*) as count FROM aircraft"
        result = execute_query(query)
        count = result['count'].values[0] if not result.empty else 0
        st.metric("Total Aircraft", count, delta=None)
    
    with col4:
        query = """
        SELECT ROUND(
            (COUNT(CASE WHEN status = 'Delayed' THEN 1 END) * 100.0) / 
            COUNT(*), 2) as delay_pct
        FROM flights WHERE status IS NOT NULL
        """
        result = execute_query(query)
        pct = result['delay_pct'].values[0] if not result.empty else 0
        st.metric("Delay Rate (%)", f"{pct}%", delta=None)
    
    st.markdown("<div class='subheader'>Flight Status Distribution</div>", unsafe_allow_html=True)
    
    # Flight Status Pie Chart
    col1, col2 = st.columns(2)
    
    with col1:
        query = """
        SELECT status, COUNT(*) as count
        FROM flights
        WHERE status IS NOT NULL
        GROUP BY status
        """
        df_status = execute_query(query)
        if not df_status.empty:
            fig = px.pie(df_status, values='count', names='status',
                        title='Flight Status Distribution',
                        color_discrete_sequence=['#2ecc71', '#e74c3c', '#f39c12'])
            st.plotly_chart(fig, use_container_width=True)
    
    # Top Airlines
    with col2:
        query = """
        SELECT airline_code, COUNT(*) as flight_count
        FROM flights
        WHERE airline_code IS NOT NULL
        GROUP BY airline_code
        ORDER BY flight_count DESC
        LIMIT 10
        """
        df_airlines = execute_query(query)
        if not df_airlines.empty:
            fig = px.bar(df_airlines, x='airline_code', y='flight_count',
                        title='Top 10 Airlines by Flight Count',
                        labels={'airline_code': 'Airline', 'flight_count': 'Flights'},
                        color='flight_count',
                        color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)

def show_airport_explorer():
    """Display airport details and search functionality"""
    st.markdown("<div class='subheader'>🏢 Airport Explorer</div>", unsafe_allow_html=True)
    
    # Get all airports
    query = "SELECT iata_code, name, city, country FROM airport ORDER BY name"
    df_airports = execute_query(query)
    
    if df_airports.empty:
        st.warning("No airport data available")
        return
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_airport = st.selectbox(
            "Select an airport",
            options=df_airports['iata_code'].tolist(),
            format_func=lambda x: f"{x} - {df_airports[df_airports['iata_code']==x]['name'].values[0]}"
        )
    
    # Display airport details
    if selected_airport:
        query = f"""
        SELECT * FROM airport 
        WHERE iata_code = '{selected_airport}'
        """
        df_airport = execute_query(query)
        
        if not df_airport.empty:
            airport = df_airport.iloc[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("IATA Code", airport['iata_code'])
            with col2:
                st.metric("City", airport['city'])
            with col3:
                st.metric("Country", airport['country'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Timezone", airport['timezone'])
            with col2:
                st.metric("Latitude", f"{airport['latitude']:.4f}")
            with col3:
                st.metric("Longitude", f"{airport['longitude']:.4f}")
            
            # Flight statistics for this airport
            st.markdown("### Flight Statistics for This Airport")
            
            col1, col2 = st.columns(2)
            
            with col1:
                query = f"""
                SELECT COUNT(*) as count FROM flights 
                WHERE origin_iata = '{selected_airport}'
                """
                departures = execute_query(query)['count'].values[0]
                st.metric("Departures", departures)
            
            with col2:
                query = f"""
                SELECT COUNT(*) as count FROM flights 
                WHERE destination_iata = '{selected_airport}'
                """
                arrivals = execute_query(query)['count'].values[0]
                st.metric("Arrivals", arrivals)
            
            # Recent flights
            st.markdown("### Recent Flights (Last 5)")
            query = f"""
            SELECT 
                f.flight_number,
                a1.name as origin,
                a2.name as destination,
                f.status,
                f.scheduled_departure
            FROM flights f
            LEFT JOIN airport a1 ON f.origin_iata = a1.iata_code
            LEFT JOIN airport a2 ON f.destination_iata = a2.iata_code
            WHERE f.destination_iata = '{selected_airport}' OR f.origin_iata = '{selected_airport}'
            ORDER BY f.scheduled_departure DESC
            LIMIT 5
            """
            df_flights = execute_query(query)
            if not df_flights.empty:
                st.dataframe(df_flights, use_container_width=True)

def show_flight_search():
    """Search and filter flights"""
    st.markdown("<div class='subheader'>🔍 Search & Filter Flights</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        flight_number = st.text_input("Flight Number", "")
    
    with col2:
        status_filter = st.selectbox(
            "Flight Status",
            ["All", "On Time", "Delayed", "Cancelled"]
        )
    
    with col3:
        airline = st.text_input("Airline Code", "")
    
    # Build query
    query = "SELECT * FROM flights WHERE 1=1"
    
    if flight_number:
        query += f" AND flight_number LIKE '%{flight_number}%'"
    
    if status_filter != "All":
        query += f" AND status = '{status_filter}'"
    
    if airline:
        query += f" AND airline_code LIKE '%{airline}%'"
    
    query += " LIMIT 100"
    
    df_flights = execute_query(query)
    
    if not df_flights.empty:
        st.dataframe(df_flights, use_container_width=True)
        st.success(f"Found {len(df_flights)} flights")
    else:
        st.info("No flights found matching the criteria")

def show_delay_analysis():
    """Display delay analysis and statistics"""
    st.markdown("<div class='subheader'>⏱️ Delay Analysis</div>", unsafe_allow_html=True)
    
    # Delay by destination airport
    query = """
    SELECT 
        a.iata_code,
        a.name,
        COUNT(f.flight_id) as total_arrivals,
        SUM(CASE WHEN f.status = 'Delayed' THEN 1 ELSE 0 END) as delayed_count,
        ROUND(
            (SUM(CASE WHEN f.status = 'Delayed' THEN 1 ELSE 0 END) * 100.0) / 
            COUNT(f.flight_id), 2
        ) as delayed_percentage
    FROM airport a
    LEFT JOIN flights f ON a.iata_code = f.destination_iata
    GROUP BY a.iata_code, a.name
    HAVING COUNT(f.flight_id) > 0
    ORDER BY delayed_percentage DESC
    """
    
    df_delays = execute_query(query)
    
    if not df_delays.empty:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.dataframe(df_delays, use_container_width=True)
        
        with col2:
            fig = px.bar(df_delays.head(10), x='iata_code', y='delayed_percentage',
                        title='Top 10 Airports by Delay Percentage',
                        labels={'iata_code': 'Airport', 'delayed_percentage': 'Delay %'},
                        color='delayed_percentage',
                        color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)

def show_route_analysis():
    """Display route analysis and busiest routes"""
    st.markdown("<div class='subheader'>🛫 Route Analysis</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    # Busiest routes
    with col1:
        query = """
        SELECT 
            a1.iata_code as origin,
            a1.city as origin_city,
            a2.iata_code as destination,
            a2.city as destination_city,
            COUNT(f.flight_id) as flight_count
        FROM flights f
        JOIN airport a1 ON f.origin_iata = a1.iata_code
        JOIN airport a2 ON f.destination_iata = a2.iata_code
        GROUP BY f.origin_iata, f.destination_iata
        ORDER BY flight_count DESC
        LIMIT 10
        """
        df_routes = execute_query(query)
        
        if not df_routes.empty:
            st.markdown("**Top 10 Busiest Routes**")
            df_routes['Route'] = df_routes['origin'] + ' → ' + df_routes['destination']
            fig = px.bar(df_routes, x='Route', y='flight_count',
                        title='Busiest Routes by Flight Count',
                        color='flight_count',
                        color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
    
    # Destination airports
    with col2:
        query = """
        SELECT 
            a.name,
            a.city,
            a.country,
            COUNT(f.flight_id) as arriving_flights
        FROM airport a
        LEFT JOIN flights f ON a.iata_code = f.destination_iata
        GROUP BY a.iata_code, a.name, a.city, a.country
        HAVING COUNT(f.flight_id) > 0
        ORDER BY arriving_flights DESC
        LIMIT 10
        """
        df_dest = execute_query(query)
        
        if not df_dest.empty:
            st.markdown("**Top 10 Destination Airports**")
            fig = px.bar(df_dest, x='name', y='arriving_flights',
                        title='Top Destination Airports',
                        color='arriving_flights',
                        color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application function"""
    
    # Sidebar Navigation
    st.sidebar.markdown("# 🌐 Navigation")
    page = st.sidebar.radio(
        "Select a page:",
        ["Home Dashboard", "Airport Explorer", "Flight Search", "Delay Analysis", "Route Analysis"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "**Air Tracker: Flight Analytics**\n\n"
        "A comprehensive aviation data analytics platform powered by AeroDataBox API.\n\n"
        "✈️ Explore airports\n"
        "🛫 Analyze flights\n"
        "⏱️ Track delays\n"
        "📊 View routes"
    )
    
    # Route to appropriate page
    if page == "Home Dashboard":
        show_home_dashboard()
    elif page == "Airport Explorer":
        show_airport_explorer()
    elif page == "Flight Search":
        show_flight_search()
    elif page == "Delay Analysis":
        show_delay_analysis()
    elif page == "Route Analysis":
        show_route_analysis()

if __name__ == "__main__":
    main()

