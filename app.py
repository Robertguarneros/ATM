import altair as alt
import pandas as pd
import streamlit as st
from functions import load_files, calculate_min_distance_to_TMR_40_24L_global
from functionsRoberto import interpolate_trajectories_global

st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

alt.themes.enable("dark")

st.title("ATM Project")

# File uploader for departures file
departures_file = st.file_uploader("Choose a departures file", key="departures_file")

# File uploader for flights file
flights_file = st.file_uploader("Choose a flights file", key="flights_file")

# Load files and calculate minimum distances
if departures_file and flights_file:
    loaded_departures, loaded_flights = load_files(departures_file, flights_file)
    minimum_distances = calculate_min_distance_to_TMR_40_24L_global(
        loaded_departures, loaded_flights
    )

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

