import altair as alt
import pandas as pd
import streamlit as st
from functionsRoberto import get_corrected_altitude_and_ias_at_threshold_global, calculate_min_distance_to_TMR_40_24L_global, load_files


# File uploader for departures file
loaded_departures, loaded_flights = load_files("assets\InputFiles\2305_02_dep_lebl.xlsx", "assets\CsvFiles\P3_04_08h.csv")
minimum_distances = calculate_min_distance_to_TMR_40_24L_global(loaded_departures, loaded_flights)

# Display the minimum distances
st.write("Minimum Distances:", minimum_distances)

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
    title="Minimum Distance to TMR-40 for Flights",
    width=1400,
    height=600
)

st.altair_chart(chart)

results = get_corrected_altitude_and_ias_at_threshold_global(loaded_departures, loaded_flights)
st.write("Results:", results)