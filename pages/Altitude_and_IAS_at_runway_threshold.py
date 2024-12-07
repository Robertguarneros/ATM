import altair as alt
import pandas as pd
import streamlit as st

from functions.functions3 import (
    get_corrected_altitude_and_ias_at_threshold_global,
    load_24h,
    load_departures,
    load_flights,
)

# Streamlit page configuration
st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Page title
st.title("Altitude and IAS at Runway Threshold")
st.write(
    "This dashboard provides insights into the Altitude and IAS at the threshold of runways 24L and 06R, including statistics, distributions, and detailed visualizations."
)

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
selected_time_frame = st.sidebar.selectbox(
    "Select Time Frame", list(time_frame_options.keys())
)
selected_flights = time_frame_options[selected_time_frame]

# Get results for runway thresholds
results = get_corrected_altitude_and_ias_at_threshold_global(
    loaded_departures, selected_flights
)
runway_options = {
    "24L": results.get("24L", []),
    "06R": results.get("06R", []),
    "24L and 06R": results,
}
selected_runway = st.sidebar.selectbox("Select Runway", list(runway_options.keys()))
selected_runway_results = runway_options[selected_runway]

# Combine results for both runways if "24L and 06R" is selected
if selected_runway == "24L and 06R":
    combined_results = results.get("24L", []) + results.get("06R", [])
    if combined_results:
        # Flatten the data structure
        flattened_results = (
            [item for sublist in combined_results for item in sublist]
            if isinstance(combined_results[0], list)
            else combined_results
        )
        df = pd.DataFrame(flattened_results)
    else:
        st.warning("No data available for either runway in the selected time frame.")
        st.stop()
else:
    if selected_runway_results:  # Check if there are results
        # Flatten the data structure
        flattened_results = (
            [item for sublist in selected_runway_results for item in sublist]
            if isinstance(selected_runway_results[0], list)
            else selected_runway_results
        )
        df = pd.DataFrame(flattened_results)
    else:
        st.warning(
            f"No data available for the selected runway ({selected_runway}) in the selected time frame. Try changing time frame or runway."
        )
        st.stop()

# Ensure 'time' exists and process it
if "time" in df.columns:
    try:
        # Convert 'time' to hours by dividing the float values by 3600
        df["time"] = df["time"].astype(float) / 3600.0
    except ValueError:
        st.error(
            "The 'time' column contains invalid values. Please check the input data."
        )
        st.stop()
else:
    st.error("The 'time' column is missing from the data. Please check the input data.")
    st.stop()

# Check if DataFrame is empty
if df.empty:
    st.warning(
        f"No flights detected for runway {selected_runway} in the selected time frame."
    )
    st.stop()

# Ensure necessary columns exist
required_columns = ["corrected_altitude", "ias", "flight_id", "time"]
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    st.error(
        f"The following columns are missing from the data: {', '.join(missing_columns)}"
    )
    st.stop()

# Summary statistics
st.subheader("Summary Statistics")
cols = st.columns(4)
cols[0].metric("Mean Altitude", f"{df['corrected_altitude'].mean():.2f} ft")
cols[1].metric("Std. Dev. Altitude", f"{df['corrected_altitude'].std():.2f} ft")
cols[2].metric("Mean IAS", f"{df['ias'].mean():.2f} knots")
cols[3].metric("Std. Dev. IAS", f"{df['ias'].std():.2f} knots")

# Divider
st.divider()

# Distributions: Histogram and Scatter Plot
st.subheader("Distributions")
col1, col2 = st.columns(2)

# Histogram of Altitude
with col1:
    st.altair_chart(
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("corrected_altitude:Q", bin=True, title="Corrected Altitude (ft)"),
            y=alt.Y("count()", title="Number of Flights"),
        )
        .properties(title="Altitude Distribution", width=400, height=400),
        use_container_width=True,
    )

# Histogram of IAS
with col2:
    st.altair_chart(
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("ias:Q", bin=True, title="IAS (knots)"),
            y=alt.Y("count()", title="Number of Flights"),
        )
        .properties(title="IAS Distribution", width=400, height=400),
        use_container_width=True,
    )

# Divider
st.divider()

# Scatter Plot of Altitude vs IAS
st.subheader("Altitude vs IAS")
st.altair_chart(
    alt.Chart(df)
    .mark_point()
    .encode(
        x=alt.X(
            "ias:Q",
            title="IAS (knots)",
            scale=alt.Scale(domain=[130, df["ias"].max()]),  # Set domain for x-axis
        ),
        y=alt.Y("corrected_altitude:Q", title="Corrected Altitude (ft)"),
        color="flight_id:N",
        tooltip=["flight_id", "corrected_altitude", "ias", "time"],
    )
    .properties(title="Altitude vs IAS", width=800, height=400),
    use_container_width=True,
)

st.divider()
# Scatter Plot of IAS vs Time
st.subheader("IAS vs Time")
st.altair_chart(
    alt.Chart(df)
    .mark_line(point=True)
    .encode(
        x=alt.X("time:Q", title="Time (hours)"),
        y=alt.Y("ias:Q", title="IAS (knots)"),
        color="flight_id:N",
        tooltip=["flight_id", "ias", "time"],
    )
    .properties(title="IAS vs Time", width=800, height=400),
    use_container_width=True,
)

# Divider
st.divider()

# Scatter Plot of Altitude vs Time
st.subheader("Altitude vs Time")
st.altair_chart(
    alt.Chart(df)
    .mark_line(point=True)
    .encode(
        x=alt.X("time:Q", title="Time (hours)"),
        y=alt.Y("corrected_altitude:Q", title="Corrected Altitude (ft)"),
        color="flight_id:N",
        tooltip=["flight_id", "corrected_altitude", "time"],
    )
    .properties(title="Altitude vs Time", width=800, height=400),
    use_container_width=True,
)
