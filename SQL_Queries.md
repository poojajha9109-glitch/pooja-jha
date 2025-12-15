# Air Tracker: Flight Analytics - SQL Queries Document

## Database Queries for Analysis

All queries execute against the flight_analytics.db SQLite database.

---

## Query 1: Total Flights by Aircraft Model

**Purpose:** Show the total number of flights for each aircraft model.

```sql
SELECT 
    ac.model,
    COUNT(f.flight_id) as total_flights
FROM flights f
JOIN aircraft ac ON f.aircraft_registration = ac.registration
GROUP BY ac.model
ORDER BY total_flights DESC;
```

---

## Query 2: Aircraft Assigned to More Than 5 Flights

**Purpose:** List all aircraft (registration, model) that have been assigned to more than 5 flights.

```sql
SELECT 
    ac.registration,
    ac.model,
    COUNT(f.flight_id) as flight_count
FROM aircraft ac
LEFT JOIN flights f ON ac.registration = f.aircraft_registration
GROUP BY ac.registration, ac.model
HAVING COUNT(f.flight_id) > 5
ORDER BY flight_count DESC;
```

---

## Query 3: Airports with More Than 5 Outbound Flights

**Purpose:** For each airport, display its name and the number of outbound flights, but only for airports with more than 5 flights.

```sql
SELECT 
    ap.iata_code,
    ap.name,
    ap.city,
    COUNT(f.flight_id) as outbound_flights
FROM airport ap
LEFT JOIN flights f ON ap.iata_code = f.origin_iata
GROUP BY ap.iata_code, ap.name, ap.city
HAVING COUNT(f.flight_id) > 5
ORDER BY outbound_flights DESC;
```

---

## Query 4: Top 3 Destination Airports by Arriving Flights

**Purpose:** Find the top 3 destination airports (name, city) by number of arriving flights.

```sql
SELECT 
    ap.name,
    ap.city,
    ap.country,
    COUNT(f.flight_id) as arriving_flights
FROM airport ap
LEFT JOIN flights f ON ap.iata_code = f.destination_iata
GROUP BY ap.iata_code, ap.name, ap.city, ap.country
HAVING COUNT(f.flight_id) > 0
ORDER BY arriving_flights DESC
LIMIT 3;
```

---

## Query 5: Domestic vs International Flights

**Purpose:** For each flight: number, origin, destination, and a label 'Domestic' or 'International' based on country match.

```sql
SELECT 
    f.flight_number,
    a1.iata_code as origin,
    a1.country as origin_country,
    a2.iata_code as destination,
    a2.country as destination_country,
    CASE 
        WHEN a1.country = a2.country THEN 'Domestic'
        ELSE 'International'
    END as flight_type
FROM flights f
JOIN airport a1 ON f.origin_iata = a1.iata_code
JOIN airport a2 ON f.destination_iata = a2.iata_code
ORDER BY f.flight_number;
```

---

## Query 6: 5 Most Recent Arrivals at DEL Airport

**Purpose:** Show the 5 most recent arrivals at DEL airport with flight details.

```sql
SELECT 
    f.flight_number,
    a1.name as departure_airport,
    a1.city as departure_city,
    f.scheduled_arrival,
    f.actual_arrival,
    ac.model as aircraft_model
FROM flights f
JOIN airport a1 ON f.origin_iata = a1.iata_code
JOIN airport a2 ON f.destination_iata = a2.iata_code
LEFT JOIN aircraft ac ON f.aircraft_registration = ac.registration
WHERE f.destination_iata = 'DEL'
ORDER BY f.actual_arrival DESC
LIMIT 5;
```

---

## Query 7: Airports with No Arriving Flights

**Purpose:** Find all airports that have never been used as a destination.

```sql
SELECT 
    ap.iata_code,
    ap.name,
    ap.city,
    ap.country
FROM airport ap
WHERE ap.iata_code NOT IN (
    SELECT DISTINCT destination_iata 
    FROM flights 
    WHERE destination_iata IS NOT NULL
)
ORDER BY ap.country, ap.city;
```

---

## Query 8: Flight Count by Status for Each Airline

**Purpose:** For each airline, count the number of flights by status.

```sql
SELECT 
    f.airline_code,
    CASE 
        WHEN f.status = 'On Time' THEN 'On Time'
        WHEN f.status = 'Delayed' THEN 'Delayed'
        WHEN f.status = 'Cancelled' THEN 'Cancelled'
        ELSE 'Other'
    END as flight_status,
    COUNT(f.flight_id) as flight_count
FROM flights f
WHERE f.airline_code IS NOT NULL
GROUP BY f.airline_code, flight_status
ORDER BY f.airline_code, flight_count DESC;
```

---

## Query 9: All Cancelled Flights

**Purpose:** Show all cancelled flights with aircraft and both airports.

```sql
SELECT 
    f.flight_number,
    a1.name as origin_airport,
    a2.name as destination_airport,
    ac.model as aircraft_model,
    ac.registration,
    f.scheduled_departure,
    f.status
FROM flights f
JOIN airport a1 ON f.origin_iata = a1.iata_code
JOIN airport a2 ON f.destination_iata = a2.iata_code
LEFT JOIN aircraft ac ON f.aircraft_registration = ac.registration
WHERE f.status = 'Cancelled'
ORDER BY f.scheduled_departure DESC;
```

---

## Query 10: City Pairs with Multiple Aircraft Models

**Purpose:** List all city pairs (origin-destination) that have more than 2 different aircraft models operating flights.

```sql
SELECT 
    a1.city as origin_city,
    a2.city as destination_city,
    COUNT(DISTINCT ac.model) as aircraft_model_count,
    GROUP_CONCAT(DISTINCT ac.model, ', ') as aircraft_models
FROM flights f
JOIN airport a1 ON f.origin_iata = a1.iata_code
JOIN airport a2 ON f.destination_iata = a2.iata_code
LEFT JOIN aircraft ac ON f.aircraft_registration = ac.registration
GROUP BY f.origin_iata, f.destination_iata
HAVING COUNT(DISTINCT ac.model) > 2
ORDER BY aircraft_model_count DESC;
```

---

## Query 11: Percentage of Delayed Flights per Destination Airport

**Purpose:** For each destination airport, compute the % of delayed flights among all arrivals.

```sql
SELECT 
    a.iata_code,
    a.name,
    a.city,
    COUNT(f.flight_id) as total_arrivals,
    SUM(CASE WHEN f.status = 'Delayed' THEN 1 ELSE 0 END) as delayed_count,
    ROUND(
        (SUM(CASE WHEN f.status = 'Delayed' THEN 1 ELSE 0 END) * 100.0) / 
        COUNT(f.flight_id), 2
    ) as delayed_percentage
FROM airport a
LEFT JOIN flights f ON a.iata_code = f.destination_iata
GROUP BY a.iata_code, a.name, a.city
HAVING COUNT(f.flight_id) > 0
ORDER BY delayed_percentage DESC;
```

---

## Additional Useful Queries

### Query 12: Summary Statistics Dashboard

```sql
SELECT 
    (SELECT COUNT(*) FROM airport) as total_airports,
    (SELECT COUNT(*) FROM flights) as total_flights,
    (SELECT COUNT(*) FROM aircraft) as total_aircraft,
    (SELECT COUNT(*) FROM flights WHERE status = 'Delayed') as delayed_flights,
    (SELECT COUNT(*) FROM flights WHERE status = 'Cancelled') as cancelled_flights,
    ROUND(
        (SELECT COUNT(*) FROM flights WHERE status = 'Delayed') * 100.0 / 
        (SELECT COUNT(*) FROM flights WHERE status IS NOT NULL), 2
    ) as delay_percentage;
```

---

### Query 13: Average Delay by Airport

```sql
SELECT 
    a.iata_code,
    a.name,
    COUNT(f.flight_id) as total_flights,
    COUNT(CASE WHEN f.status = 'Delayed' THEN 1 END) as delayed_flights,
    ROUND(
        (COUNT(CASE WHEN f.status = 'Delayed' THEN 1 END) * 100.0) / 
        COUNT(f.flight_id), 2
    ) as delay_percentage
FROM airport a
LEFT JOIN flights f ON a.iata_code = f.destination_iata
GROUP BY a.iata_code, a.name
HAVING COUNT(f.flight_id) > 0
ORDER BY delay_percentage DESC;
```

---

### Query 14: Busiest Routes (Most Flights)

```sql
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
LIMIT 10;
```

---

### Query 15: Airline Performance Summary

```sql
SELECT 
    f.airline_code,
    COUNT(f.flight_id) as total_flights,
    SUM(CASE WHEN f.status = 'On Time' THEN 1 ELSE 0 END) as on_time,
    SUM(CASE WHEN f.status = 'Delayed' THEN 1 ELSE 0 END) as delayed,
    SUM(CASE WHEN f.status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled,
    ROUND(
        (SUM(CASE WHEN f.status = 'On Time' THEN 1 ELSE 0 END) * 100.0) / 
        COUNT(f.flight_id), 2
    ) as on_time_percentage
FROM flights f
WHERE f.airline_code IS NOT NULL
GROUP BY f.airline_code
ORDER BY on_time_percentage DESC;
```

---

## Query Execution Tips

1. **Always verify data exists** before running complex queries
2. **Use LIMIT** for initial testing to avoid large result sets
3. **Check NULL values** - use `IS NOT NULL` in WHERE clauses appropriately
4. **Monitor performance** - create indexes on frequently queried columns
5. **Use EXPLAIN QUERY PLAN** for query optimization

## Example: Check if data exists
```sql
SELECT COUNT(*) as record_count FROM flights;
SELECT COUNT(*) as airport_count FROM airport;
SELECT COUNT(*) as aircraft_count FROM aircraft;
```

---

**Document Version:** 1.0  
**Last Updated:** December 2025  
**Database:** flight_analytics.db (SQLite)
