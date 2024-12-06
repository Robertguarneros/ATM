import altair as alt
import pandas as pd
import streamlit as st
from functions.functions3 import load_departures, load_flights, load_24h, get_corrected_altitude_and_ias_at_threshold_global

# Page title
st.title("Altitude and IAS at Runway Threshold")
st.write("This dashboard provides insights into the Altitude and IAS at the threshold of runways 24L and 06R, including statistics, distributions, and detailed visualizations.")

# Load data
loaded_departures = load_departures("assets/InputFiles/2305_02_dep_lebl.xlsx")
loaded_flights_00_04 = load_flights("assets/CsvFiles/P3_00_04h.csv")
loaded_flights_04_08 = load_flights("assets/CsvFiles/P3_04_08h.csv")
loaded_flights_08_12 = load_flights("assets/CsvFiles/P3_08_12h.csv")
loaded_flights_12_16 = load_flights("assets/CsvFiles/P3_12_16h.csv")
loaded_flights_16_20 = load_flights("assets/CsvFiles/P3_16_20h.csv")
loaded_flights_20_24 = load_flights("assets/CsvFiles/P3_20_24h.csv")
loaded_all_flights = load_24h("assets/CsvFiles/P3_00_04h.csv",
                              "assets/CsvFiles/P3_04_08h.csv",
                              "assets/CsvFiles/P3_08_12h.csv",
                              "assets/CsvFiles/P3_12_16h.csv",
                              "assets/CsvFiles/P3_16_20h.csv",
                              "assets/CsvFiles/P3_20_24h.csv")

# Time frame selector
time_frame_options = {
    "From 00:00 to 04:00": loaded_flights_00_04,
    "From 04:00 to 08:00": loaded_flights_04_08,
    "From 08:00 to 12:00": loaded_flights_08_12,
    "From 12:00 to 16:00": loaded_flights_12_16,
    "From 16:00 to 20:00": loaded_flights_16_20,
    "From 20:00 to 24:00": loaded_flights_20_24,
    "Whole Day": loaded_all_flights
}
selected_time_frame = st.selectbox("Select Time Frame", list(time_frame_options.keys()))
selected_flights = time_frame_options[selected_time_frame]

results = get_corrected_altitude_and_ias_at_threshold_global(loaded_departures, selected_flights)

runway_options = {
    "24L": "24L",
    "06R": "06R",
}

selected_runway = st.selectbox("Select Runway", list(runway_options.keys()))
selected_runway_results = runway_options[selected_runway]

st.write(f"### {selected_runway} Results")
st.write(results[selected_runway])