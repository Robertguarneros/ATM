import streamlit as st
import altair as alt
import pandas as pd
from functions.functions1 import load_flights, load_24h, general, compare_radar_separation, compare_wake_separation, compare_loa_separation

# Streamlit page configuration
st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",  # Permite usar todo el ancho de la página
    initial_sidebar_state="expanded",
)

st.title("ATM Project - Separation Losses")
st.write("Here you can see the distance between flights when taking off.")
st.write("You can filter by Radar, Wake, or LoA.")
st.divider()
st.subheader("Radar Comparation")


# Load data
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
    "assets/CsvFiles/P3_20_24h.csv",
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

results_24L, results_06R, flight_info = general(selected_flights)

runway_options = {"24L": results_24L, "06R": results_06R}
selected_runway = st.sidebar.selectbox("Select Runway", list(runway_options.keys()))
selected_runway_results = runway_options[selected_runway]

# Process results
results_radar, per_radar = compare_radar_separation(selected_runway_results)

# Convert results to DataFrame
df_bars = pd.DataFrame(results_radar, columns=["Front Flight", "Rear Flight", "Distance (NM)", "Compliant"])

# Dashboard layout
col1, col2 = st.columns(2)

# Column 1: Bar chart (separation distance)
with col1:

    st.subheader("Statistics for Distance Between Flights")
    if not df_bars.empty:
        mean_distance = df_bars["Distance (NM)"].mean()
        std_distance = df_bars["Distance (NM)"].std()
        median_distance = df_bars["Distance (NM)"].median()

        col3, col4 = st.columns(2)
        with col3:
            st.metric("Mean (Average)", f"{mean_distance:.2f} NM")
            st.metric("Standard Deviation", f"{std_distance:.2f} NM")

        with col4:
            st.metric("Median", f"{median_distance:.2f} NM")
    else:
        st.write("No data available for statistics.")

# Column 2: Pie chart and statistics
with col2:
    st.subheader("Compliance Percentage")
    compliance_data = pd.DataFrame({
        "Category": ["Compliant", "Non-Compliant"],
        "Percentage": [per_radar, 100 - per_radar],
    })

    pie_chart = alt.Chart(compliance_data).mark_arc().encode(
        theta=alt.Theta("Percentage:Q", title="Percentage"),
        color=alt.Color("Category:N", scale=alt.Scale(range=["steelblue", "orange"])),
        tooltip=["Category", "Percentage"],
    ).properties(
        title="Compliance Percentage",
        width=300,
        height=300,
    )
    st.altair_chart(pie_chart, use_container_width=True)

   
st.subheader("Separation Distance Between Flights")
if not df_bars.empty:
    # Bar chart
    bar_chart = alt.Chart(df_bars).mark_bar().encode(
        x=alt.X("Rear Flight:N", title="Rear Flight"),
        y=alt.Y("Distance (NM):Q", title="Distance (NM)"),
        color=alt.condition(
            alt.datum.Compliant,
            alt.value("steelblue"),  # Compliant
            alt.value("orange"),  # Non-compliant
        ),
        tooltip=["Front Flight", "Rear Flight", "Distance (NM)", "Compliant"],
    ).properties(
        width=400,
        height=300,
        title="Distance Between Flights",
    )

    # Add red line for threshold
    line = alt.Chart(pd.DataFrame({"y": [3]})).mark_rule(color="red").encode(y="y:Q")
    final_chart = bar_chart + line
    st.altair_chart(final_chart, use_container_width=True)
else:
    st.write("No data available for the selected filters.")

st.divider()
