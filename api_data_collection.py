# Air Tracker: Flight Analytics - API Data Collection Script
# Purpose: Extract aviation data from AeroDataBox API and populate SQL database

import requests
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# ============================================================================
# API Configuration
# ============================================================================

API_HOST = "aerodatabox.p.rapidapi.com"
API_KEY = "YOUR_RAPIDAPI_KEY"  # Replace with your RapidAPI key

HEADERS = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': API_HOST
}

# Sample Airport Codes (10-15 major airports)
AIRPORT_CODES = [
    'DEL', 'BOM', 'BLR', 'CCU', 'HYD',  # India
    'LHR', 'CDG', 'DXB', 'SIN', 'HND',  # International
    'LAX', 'JFK', 'ORD'                 # USA
]

# ============================================================================
# Database Setup
# ============================================================================

def create_database(db_name: str = 'flight_analytics.db'):
    """Create SQLite database with required schema"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Airport Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS airport (
        airport_id INTEGER PRIMARY KEY AUTOINCREMENT,
        icao_code TEXT UNIQUE,
        iata_code TEXT UNIQUE,
        name TEXT,
        city TEXT,
        country TEXT,
        continent TEXT,
        latitude REAL,
        longitude REAL,
        timezone TEXT
    )
    ''')
    
    # Aircraft Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS aircraft (
        aircraft_id INTEGER PRIMARY KEY AUTOINCREMENT,
        registration TEXT UNIQUE,
        model TEXT,
        manufacturer TEXT,
        icao_type_code TEXT,
        owner TEXT
    )
    ''')
    
    # Flights Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS flights (
        flight_id TEXT PRIMARY KEY,
        flight_number TEXT,
        aircraft_registration TEXT,
        origin_iata TEXT,
        destination_iata TEXT,
        scheduled_departure TEXT,
        actual_departure TEXT,
        scheduled_arrival TEXT,
        actual_arrival TEXT,
        status TEXT,
        airline_code TEXT,
        FOREIGN KEY(origin_iata) REFERENCES airport(iata_code),
        FOREIGN KEY(destination_iata) REFERENCES airport(iata_code),
        FOREIGN KEY(aircraft_registration) REFERENCES aircraft(registration)
    )
    ''')
    
    # Airport Delays Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS airport_delays (
        delay_id INTEGER PRIMARY KEY AUTOINCREMENT,
        airport_iata TEXT,
        delay_date TEXT,
        total_flights INTEGER,
        delayed_flights INTEGER,
        avg_delay_min INTEGER,
        median_delay_min INTEGER,
        canceled_flights INTEGER,
        FOREIGN KEY(airport_iata) REFERENCES airport(iata_code)
    )
    ''')
    
    conn.commit()
    return conn

# ============================================================================
# API Data Extraction Functions
# ============================================================================

def get_airport_info(iata_code: str) -> Optional[Dict]:
    """Fetch airport information from AeroDataBox API"""
    try:
        url = f"https://{API_HOST}/airports/iata/{iata_code}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching airport {iata_code}: {e}")
        return None

def get_flights_by_airport(iata_code: str, direction: str = 'departures') -> Optional[List[Dict]]:
    """
    Fetch flights for an airport
    direction: 'departures' or 'arrivals'
    """
    try:
        # Get flights from past 24 hours to past 7 days
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=3)
        
        url = f"https://{API_HOST}/airports/iata/{iata_code}/{direction}/latest"
        params = {
            'withLeg': 'true',
            'direction': direction
        }
        
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        
        return data.get(direction, [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {direction} for {iata_code}: {e}")
        return None

def get_aircraft_info(registration: str) -> Optional[Dict]:
    """Fetch aircraft detailed information"""
    try:
        url = f"https://{API_HOST}/aircrafts/iata/{registration}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching aircraft {registration}: {e}")
        return None

# ============================================================================
# Data Insertion Functions
# ============================================================================

def insert_airport(conn, airport_data: Dict):
    """Insert airport data into database"""
    try:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO airport 
        (icao_code, iata_code, name, city, country, continent, latitude, longitude, timezone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            airport_data.get('icao'),
            airport_data.get('iata'),
            airport_data.get('name'),
            airport_data.get('city'),
            airport_data.get('country'),
            airport_data.get('continent'),
            airport_data.get('latitude'),
            airport_data.get('longitude'),
            airport_data.get('timezone')
        ))
        conn.commit()
    except Exception as e:
        print(f"Error inserting airport: {e}")

def insert_aircraft(conn, aircraft_data: Dict):
    """Insert aircraft data into database"""
    try:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO aircraft 
        (registration, model, manufacturer, icao_type_code, owner)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            aircraft_data.get('registration'),
            aircraft_data.get('model'),
            aircraft_data.get('manufacturer'),
            aircraft_data.get('icaoTypeCode'),
            aircraft_data.get('owner')
        ))
        conn.commit()
    except Exception as e:
        print(f"Error inserting aircraft: {e}")

def insert_flight(conn, flight_data: Dict):
    """Insert flight data into database"""
    try:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO flights 
        (flight_id, flight_number, aircraft_registration, origin_iata, 
         destination_iata, scheduled_departure, actual_departure, 
         scheduled_arrival, actual_arrival, status, airline_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            flight_data.get('number'),  # flight_id
            flight_data.get('number'),  # flight_number
            flight_data.get('aircraft', {}).get('registration'),
            flight_data.get('departure', {}).get('airport', {}).get('iata'),
            flight_data.get('arrival', {}).get('airport', {}).get('iata'),
            flight_data.get('departure', {}).get('scheduledTimeUtc'),
            flight_data.get('departure', {}).get('actualTimeUtc'),
            flight_data.get('arrival', {}).get('scheduledTimeUtc'),
            flight_data.get('arrival', {}).get('actualTimeUtc'),
            flight_data.get('status'),
            flight_data.get('airline', {}).get('iata')
        ))
        conn.commit()
    except Exception as e:
        print(f"Error inserting flight: {e}")

# ============================================================================
# Main Data Collection Pipeline
# ============================================================================

def main():
    """Main data collection workflow"""
    print("=== Air Tracker: Flight Analytics - Data Collection ===\n")
    
    # Step 1: Create Database
    print("Step 1: Creating database schema...")
    conn = create_database()
    print("✓ Database created successfully\n")
    
    # Step 2: Fetch Airport Data
    print("Step 2: Fetching airport information...")
    airports_data = {}
    for iata in AIRPORT_CODES:
        print(f"  Fetching data for airport: {iata}")
        airport_info = get_airport_info(iata)
        if airport_info:
            insert_airport(conn, airport_info)
            airports_data[iata] = airport_info
            print(f"  ✓ {airport_info.get('name')} - {airport_info.get('city')}")
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n✓ Fetched {len(airports_data)} airports\n")
    
    # Step 3: Fetch Flights Data
    print("Step 3: Fetching flight information...")
    aircraft_registrations = set()
    
    for iata in airports_data.keys():
        print(f"  Fetching departures from {iata}...")
        departures = get_flights_by_airport(iata, 'departures')
        if departures:
            for flight in departures[:5]:  # Limit to 5 flights per airport
                insert_flight(conn, flight)
                if flight.get('aircraft', {}).get('registration'):
                    aircraft_registrations.add(flight['aircraft']['registration'])
        time.sleep(0.5)
    
    print(f"✓ Fetched flights data\n")
    
    # Step 4: Fetch Aircraft Data
    print("Step 4: Fetching aircraft information...")
    for registration in list(aircraft_registrations)[:10]:  # Limit to 10 aircraft
        print(f"  Fetching data for aircraft: {registration}")
        aircraft_info = get_aircraft_info(registration)
        if aircraft_info:
            insert_aircraft(conn, aircraft_info)
            print(f"  ✓ {aircraft_info.get('model')}")
        time.sleep(0.5)
    
    print(f"\n✓ Data collection complete!\n")
    
    # Summary
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM airport")
    airport_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM flights")
    flight_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM aircraft")
    aircraft_count = cursor.fetchone()[0]
    
    print("=== Database Summary ===")
    print(f"Total Airports: {airport_count}")
    print(f"Total Flights: {flight_count}")
    print(f"Total Aircraft: {aircraft_count}")
    
    conn.close()
    print("\n✓ Database saved as 'flight_analytics.db'")

if __name__ == "__main__":
    main()
