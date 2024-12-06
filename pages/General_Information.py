import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from functions.functions3 import (
    load_departures,
    load_flights,
    load_24h,
    get_trajectory_for_airplane,
    filter_empty_trajectories,
    filter_departures_by_runway,
    correct_altitude_for_file,
    filter_trajectories_by_runway
)

# Streamlit page configuration
st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("General Information")

# Load data
loaded_departures = load_departures("assets/InputFiles/2305_02_dep_lebl.xlsx")
loaded_flights_00_04 = load_flights("assets/CsvFiles/P3_00_04h.csv")
loaded_flights_04_08 = load_flights("assets/CsvFiles/P3_04_08h.csv")
loaded_flights_08_12 = load_flights("assets/CsvFiles/P3_08_12h.csv")
loaded_flights_12_16 = load_flights("assets/CsvFiles/P3_12_16h.csv")
loaded_flights_16_20 = load_flights("assets/CsvFiles/P3_16_20h.csv")
loaded_flights_20_24 = load_flights("assets/CsvFiles/P3_20_24h.csv")
loaded_all_flights = load_24h(
    "assets/CsvFiles/P3_00_04h.csv",
    "assets/CsvFiles/P3_04_08h.csv",
    "assets/CsvFiles/P3_08_12h.csv",
    "assets/CsvFiles/P3_12_16h.csv",
    "assets/CsvFiles/P3_16_20h.csv",
    "assets/CsvFiles/P3_20_24h.csv"
)

# Time frame selector
st.sidebar.header("Filters")
time_frame_options = {
    "From 00:00 to 04:00": loaded_flights_00_04,
    "From 04:00 to 08:00": loaded_flights_04_08,
    "From 08:00 to 12:00": loaded_flights_08_12,
    "From 12:00 to 16:00": loaded_flights_12_16,
    "From 16:00 to 20:00": loaded_flights_16_20,
    "From 20:00 to 24:00": loaded_flights_20_24,
    "Whole Day": loaded_all_flights,
}
selected_time_frame = st.sidebar.selectbox("Select Time Frame", list(time_frame_options.keys()))
selected_flights = time_frame_options[selected_time_frame]

# Process data
departures_6R, departures_24L = filter_departures_by_runway(loaded_departures, selected_flights)
corrected_alitude_matrix = correct_altitude_for_file(selected_flights)
trajectories = get_trajectory_for_airplane(loaded_departures, corrected_alitude_matrix)
filtered_trajectories = filter_empty_trajectories(trajectories)
filtered_trajectories_24L, filtered_trajectories_06R = filter_trajectories_by_runway(
    filtered_trajectories, departures_24L, departures_6R
)

# Merge dictionaries for both runways
results = {**filtered_trajectories_24L, **filtered_trajectories_06R}

runway_options = {
    "24L": filtered_trajectories_24L,
    "06R": filtered_trajectories_06R,
    "All runways": results
}

st.divider()
st.subheader("Flight Distribution")

# Prepare data for pie chart: distribution of flights per runway
flight_counts = {
    "24L": len(filtered_trajectories_24L),
    "06R": len(filtered_trajectories_06R),
}
fig_pie = go.Figure(
    data=[go.Pie(labels=list(flight_counts.keys()), values=list(flight_counts.values()))]
)
fig_pie.update_layout(title="Distribution of Flights per Runway")
st.plotly_chart(fig_pie, use_container_width=True)

# Prepare data for bar chart: distribution of flights per hour
flight_hours = []  # Store the hour of the first timestamp for each flight

for trajectory in filtered_trajectories.values():  # Combine all flights
    if trajectory:  # Ensure the trajectory is not empty
        first_point = trajectory[0]  # Take the first point of the flight
        flight_hours.append(int(first_point["time"]) // 3600)  # Convert time to hours

# Group flights by hour
flight_hours_df = pd.DataFrame(flight_hours, columns=["hour"])
flight_hour_counts = flight_hours_df["hour"].value_counts().sort_index()

# Create bar chart
fig_bar = go.Figure(
    data=[
        go.Bar(
            x=flight_hour_counts.index,
            y=flight_hour_counts.values,
            text=flight_hour_counts.values,
            textposition="auto",
        )
    ]
)
fig_bar.update_layout(
    title="Distribution of Flights per Hour",
    xaxis_title="Hour of Day (UTC)",
    yaxis_title="Number of Flights",
)
st.plotly_chart(fig_bar, use_container_width=True)

st.divider()
# Page title
st.subheader("Departures Trajectories")
selected_runway = st.selectbox("Select Runway", list(runway_options.keys()))
selected_runway_results = runway_options[selected_runway]
# Handle case when there are no flights
if not selected_runway_results:
    st.warning("No flight trajectories available for the selected runway and time frame.")
else:
    # Plotly Visualization
    fig = go.Figure()

    # Add each trajectory to the map
    for flight_id, flight_data in selected_runway_results.items():
        lats = [float(point["latitude"]) for point in flight_data]
        lons = [float(point["longitude"]) for point in flight_data]
        fig.add_trace(
            go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode="lines+markers",
                marker=dict(size=5),
                line=dict(width=2),
                name=f"Flight {flight_id}",
            )
        )

    # Update map layout
    # Update map layout with a specific size
    fig.update_layout(
    mapbox=dict(
        style="carto-positron",  # Light map style
        center={"lat": 41.298123, "lon": 2.080165},  # Center map at Barcelona Airport
        zoom=10,
    ),
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    width=1200,  # Set the desired width of the map
    height=600,  # Set the desired height of the map
    showlegend=True,
)

    # Display the map
    st.plotly_chart(fig, use_container_width=True)
