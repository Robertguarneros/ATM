import altair as alt
import pandas as pd
import streamlit as st
from functions.functions3 import calculate_min_distance_to_TMR_40_24L_global, load_departures, load_flights, load_24h

# Streamlit page configuration
st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Page title
st.title("Horizontal Distance to TMR-40 for Departures from 24L")
st.write("This dashboard provides insights into the horizontal distance to TMR-40 for departures from runway 24L, including statistics, distributions, and detailed visualizations.")

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

# Calculate minimum distances
minimum_distances = calculate_min_distance_to_TMR_40_24L_global(loaded_departures, selected_flights)
df = pd.DataFrame({
    "Flight ID": list(minimum_distances.keys()),
    "Minimum Distance (NM)": [value[0] for value in minimum_distances.values()],
    "Time (seconds)": [value[1] for value in minimum_distances.values()]
})
df["Time (seconds)"] = pd.to_numeric(df["Time (seconds)"], errors="coerce")
df = df.dropna(subset=["Time (seconds)"])
df["Time (hours)"] = (df["Time (seconds)"] // 3600).astype(int)

# Group by hourly intervals
df_grouped = df.groupby("Time (hours)").agg({
    "Minimum Distance (NM)": ["mean", "count"]
}).reset_index()
df_grouped.columns = ["Time (hours)", "Mean Distance (NM)", "Number of Flights"]

# Layout: Summary statistics
st.subheader("Summary Statistics")
cols = st.columns(4)
cols[0].metric("Mean Distance (NM)", f"{df['Minimum Distance (NM)'].mean():.2f}")
cols[1].metric("Median Distance (NM)", f"{df['Minimum Distance (NM)'].median():.2f}")
cols[2].metric("Mode Distance (NM)", f"{df['Minimum Distance (NM)'].mode()[0]:.2f}")
cols[3].metric("Std. Deviation (NM)", f"{df['Minimum Distance (NM)'].std():.2f}")

st.divider()  # Add a visual divider between sections

# Layout: Histogram and Pie chart in two columns
st.subheader("Distributions")
col1, col2 = st.columns(2)

# Histogram
with col1:
    st.altair_chart(
        alt.Chart(df).mark_bar().encode(
            x=alt.X("Minimum Distance (NM):Q", bin=True, title="Minimum Distance (NM)"),
            y=alt.Y("count()", title="Number of Flights")
        ).properties(
            title="Distribution of Minimum Distances",
            width=400,
            height=400
        ),
        use_container_width=True
    )

# Pie chart
with col2:
    bins = [i * 0.1 for i in range(21)]  # Define 0.1 NM intervals
    ranges = pd.cut(df["Minimum Distance (NM)"], bins=bins, include_lowest=True)
    range_labels = [f"{round(interval.left, 1)}-{round(interval.right, 1)}" for interval in ranges.cat.categories]
    ranges = ranges.cat.rename_categories(range_labels)
    range_counts = ranges.value_counts(normalize=True).reset_index()
    range_counts.columns = ["Range", "Percentage"]
    range_counts["Percentage"] *= 100  # Convert to percentage
    st.altair_chart(
        alt.Chart(range_counts).mark_arc(innerRadius=50).encode(
            theta=alt.Theta("Percentage:Q", title="Percentage of Flights"),
            color=alt.Color("Range:N", title="Distance Range"),
            tooltip=["Range:N", "Percentage:Q"]
        ).properties(
            title="Percentage of Flights (0 to 2 NM)",
            width=400,
            height=500
        ),
        use_container_width=True
    )

st.divider()  # Another divider

# Line chart for flights over time
st.subheader(f"Minimum Distance to TMR-40 for Flights ({selected_time_frame})")
st.altair_chart(
    alt.Chart(df).mark_line().encode(
        x=alt.X("Flight ID:N", title="Flight ID"),
        y=alt.Y("Minimum Distance (NM):Q", title="Minimum Distance (NM)"),
        tooltip=["Flight ID", "Minimum Distance (NM)"]
    ).properties(
        title="Minimum Distance to TMR-40 by Flight",
        width=1400,
        height=600
    ),
    use_container_width=True
)

# Add bar chart for hourly mean distances
st.subheader(f"Minimum Distance by 1-Hour Intervals ({selected_time_frame})")
st.altair_chart(
    alt.Chart(df_grouped).mark_bar().encode(
        x=alt.X("Time (hours):Q", title="Time (hours)"),
        y=alt.Y("Mean Distance (NM):Q", title="Mean Distance (NM)"),
        tooltip=["Time (hours)", "Mean Distance (NM)", "Number of Flights"]
    ).properties(
        title="Mean Distance by Hourly Intervals",
        width=800,
        height=400
    ),
    use_container_width=True
)
