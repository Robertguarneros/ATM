import streamlit as st
import pandas as pd
import numpy as np
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

# Page title
st.title("Departures Trajectories")

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
    "24L and 06R": results
}
selected_runway = st.sidebar.selectbox("Select Runway", list(runway_options.keys()))
selected_runway_results = runway_options[selected_runway]

# Prepare data for map visualization
all_trajectory_points = []

for flight_id, flight_data in selected_runway_results.items():
    for point in flight_data:
        all_trajectory_points.append({
            "latitude": float(point["latitude"]),
            "longitude": float(point["longitude"]),
        })

trajectory_df = pd.DataFrame(all_trajectory_points)

# Display the map
if not trajectory_df.empty:
    st.map(trajectory_df, zoom=10, use_container_width=True)
else:
    st.warning("No trajectory data available for the selected runway and time frame.")
