import altair as alt
import pandas as pd
import streamlit as st
from functions.functions3 import get_corrected_altitude_and_ias_at_threshold_global, calculate_min_distance_to_TMR_40_24L_global, load_departures, load_flights, load_24h

# File uploader for departures file
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

# Mapping of time frame options to loaded flights
time_frame_options = {
    "From 00:00 to 04:00": loaded_flights_00_04,
    "From 04:00 to 08:00": loaded_flights_04_08,
    "From 08:00 to 12:00": loaded_flights_08_12,
    "From 12:00 to 16:00": loaded_flights_12_16,
    "From 16:00 to 20:00": loaded_flights_16_20,
    "From 20:00 to 24:00": loaded_flights_20_24,
    "Whole Day": loaded_all_flights
}

# Streamlit selector for time frame
selected_time_frame = st.selectbox(
    "Select Time Frame",
    list(time_frame_options.keys())
)

# Get the selected flights data
selected_flights = time_frame_options[selected_time_frame]

# Calculate minimum distances for the selected time frame
minimum_distances = calculate_min_distance_to_TMR_40_24L_global(loaded_departures, selected_flights)

# Convert the minimum distances dictionary to a DataFrame
df = pd.DataFrame({
    "Flight ID": list(minimum_distances.keys()),
    "Minimum Distance (NM)": list(minimum_distances.values())
})

# Sort the DataFrame by distance for better visualization
df = df.sort_values(by="Minimum Distance (NM)")

# Altair chart for better customization
chart = alt.Chart(df).mark_line().encode(
    x="Flight ID:N",  # Nominal (categorical) axis
    y="Minimum Distance (NM):Q"  # Quantitative axis
).properties(
    title=f"Minimum Distance to TMR-40 for Flights ({selected_time_frame})",
    width=1400,
    height=600
)

st.altair_chart(chart)
