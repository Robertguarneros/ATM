import altair as alt
import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from folium import CircleMarker, Map, PolyLine
from streamlit.components.v1 import html

from functions.functions2 import (
    correct_altitude_for_file,
    crosses_fixed_radial,
    dms_to_decimal,
    extract_turn,
    load_24h,
    load_departures,
    load_flights,
    trajectories_turn_24L,
)

# Streamlit page configuration
st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title("Turn data")
st.write("Here we can see info about the turns when departing from runway 24L")

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

f = correct_altitude_for_file(selected_flights)
trajectories = trajectories_turn_24L(f, loaded_departures)
turns = extract_turn(loaded_departures, f)

if not trajectories:
    st.warning(
        f"No flights took off from runway 24L during the selected time frame ({selected_time_frame})"
    )
else:
    all_coords = [
        (float(p["latitude"]), float(p["longitude"]))
        for points in trajectories.values()
        for p in points
    ]

    # Mean lat and lon
    if all_coords:
        mean_lat = sum(coord[0] for coord in all_coords) / len(all_coords)
        mean_lon = sum(coord[1] for coord in all_coords) / len(all_coords)
    else:
        mean_lat, mean_lon = 41.3, 2.1

    # Coordinates DVOR BCN
    lat_dvor_bcn = dms_to_decimal(41, 18, 25.6)
    lon_dvor_bcn = dms_to_decimal(2, 6, 28.1)

    # Coordinates Point
    lat_punto_costas = dms_to_decimal(41, 16, 5.4)
    lon_punto_costas = dms_to_decimal(2, 2, 0.0)

    # Create a map centered
    m = Map(
        location=[
            (mean_lat + lat_dvor_bcn + lat_punto_costas) / 3,
            (mean_lon + lon_dvor_bcn + lon_punto_costas) / 3,
        ],
        zoom_start=13,
    )

    # Plot a line between the two points
    PolyLine(
        locations=[[lat_dvor_bcn, lon_dvor_bcn], [lat_punto_costas, lon_punto_costas]],
        color="green",
        weight=3,
    ).add_to(m)

    # Add aircraft trajectories
    for flight, points in trajectories.items():
        # Extract trajectories coordinates
        trajectory_coords = [
            (float(p["latitude"]), float(p["longitude"])) for p in points
        ]

        # Draw trajectory
        PolyLine(
            locations=trajectory_coords,
            color="purple",
            weight=0.5,
            tooltip=f"Trayectoria del vuelo {flight}",
        ).add_to(m)

    # Show map in Streamlit
    st.subheader("Map with take-off trajectories")
    # Check if there are flights crossing the radial
    results = crosses_fixed_radial(trajectories)
    flights_crossing_radial = [flight for flight, crossed in results.items() if crossed]

    if len(flights_crossing_radial) == 0:
        st.markdown(
            "<div style='background-color: #d4edda; padding: 8px; border-radius: 5px; height: 35px;'><h6 style='font-weight: normal; color: grey;'>No flights cross the radial during their initial turn   ✔️</h6></div>",
            unsafe_allow_html=True,
        )
    else:
        # If there are flights crossing the radial, show affected flights with bold and red color
        st.warning(
            f"The following flight(s) cross the radial during their initial turn at takeoff:{', '.join(flights_crossing_radial)}",
        )

    html_str = m._repr_html_()
    html(html_str, height=500)

    st.divider()

    # Summary statistics
    st.subheader("Summary Statistics for Initial Turning Point")

    # Create a DataFrame
    columns = ["Aircraft_ID", "Latitude", "Longitude", "Altitude"]
    df = pd.DataFrame(turns, columns=columns)
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df["Altitude"] = pd.to_numeric(df["Altitude"], errors="coerce")

    df_clean = df.dropna(subset=["Latitude", "Longitude", "Altitude"])

    # Define a function to display metrics
    def display_metrics(df_clean, column_name, label):
        cols = st.columns(5)
        cols[0].markdown(
            "<br>", unsafe_allow_html=True
        )  # Adds vertical space to "center" the text vertically
        cols[0].markdown(f"##### {label}")
        cols[1].metric(f"Mean {column_name}", f"{df[column_name].mean():.2f}")
        cols[2].metric(f"Median {column_name}", f"{df[column_name].median():.2f}")
        mode = df[column_name].mode()
        mode_value = mode.iloc[0] if not mode.empty else "nan"
        cols[3].metric(
            f"Mode {column_name}",
            f"{mode_value:.2f}" if mode_value != "nan" else mode_value,
        )
        cols[4].metric(f"Std. Deviation {column_name}", f"{df[column_name].std():.2f}")

    # Display metrics for Latitude
    display_metrics(df_clean, "Latitude", "Latitude (°)")

    # Display metrics for Longitude
    display_metrics(df_clean, "Longitude", "Longitude (°)")

    # Display metrics for Altitude
    display_metrics(df_clean, "Altitude", "Altitude (ft)")

    st.divider()

    altitude_bins = [(0, 500), (500, 1000), (1000, 1500)]
    bin_labels = ["0-500ft", "500-1000ft", "1000-1500ft"]

    # Create a new column in the dataframe for altitude ranges
    def get_altitude_range(altitude):
        for i, (low, high) in enumerate(altitude_bins):
            if low <= altitude < high:
                return bin_labels[i]
        return "Unknown"

    df_clean["Altitude Range"] = df_clean["Altitude"].apply(get_altitude_range)

    # Layout: Histogram and Pie chart in two columns
    st.subheader("Altitude Distributions")
    col1, col2 = st.columns(2)

    # Histogram for Altitude Distribution
    with col1:
        st.altair_chart(
            alt.Chart(df_clean)
            .mark_bar()
            .encode(
                x=alt.X("Altitude:Q", bin=alt.Bin(maxbins=30), title="Altitude (ft)"),
                y=alt.Y("count()", title="Number of Flights"),
                tooltip=["Altitude", "count()"],
            )
            .properties(title="Altitude Distribution by Flight", width=400, height=400),
            use_container_width=True,
        )

    # Pie chart for Percentage of Flights in Different Altitude Ranges
    with col2:
        # Count the number of flights in each altitude range
        range_counts = (
            df_clean["Altitude Range"].value_counts(normalize=True).reset_index()
        )
        range_counts.columns = ["Range", "Percentage"]
        range_counts["Percentage"] *= 100  # Convert to percentage

        st.altair_chart(
            alt.Chart(range_counts)
            .mark_arc(innerRadius=50)
            .encode(
                theta=alt.Theta("Percentage:Q", title="Percentage of Flights"),
                color=alt.Color("Range:N", title="Altitude Range"),
                tooltip=["Range:N", "Percentage:Q"],
            )
            .properties(
                title="Percentage of Flights in Different Altitude Ranges",
                width=400,
                height=400,
            ),
            use_container_width=True,
        )

    st.divider()  # Add a visual divider between sections

    st.subheader("Map with Initial Turning Points")

    m = folium.Map(
        location=[df_clean["Latitude"].mean(), df_clean["Longitude"].mean()],
        zoom_start=14,
    )

    # Iterate over the flight trajectories
    for flight, points in trajectories.items():
        # Extract the coordinates from the trajectory
        trajectory_coords = [
            (float(p["latitude"]), float(p["longitude"])) for p in points
        ]

        # Draw the trajectory as a purple polyline on the map
        PolyLine(
            locations=trajectory_coords,
            color="purple",  # Set the polyline color to purple
            weight=0.5,
            tooltip=f"Flight trajectory for flight {flight}",  # Tooltip with flight information
        ).add_to(m)

        # Add a marker with information for each point in the dataframe
        for _, row in df_clean.iterrows():
            lat = row["Latitude"]  # Latitude of the point
            lon = row["Longitude"]  # Longitude of the point
            al = row["Altitude"]  # Altitude of the point
            aircraft_id = row["Aircraft_ID"]

            # Create the text for the tooltip containing the point information
            tooltip_text = (
                f"Lat: {lat}°, Lon: {lon}°, Alt: {al} ft, Aircraft ID: {aircraft_id}"
            )

            # Create a circle marker with the tooltip for each point
            CircleMarker(
                location=[lat, lon],  # Position the marker at the point's coordinates
                radius=5,
                fill=True,
                fill_opacity=0.6,
                tooltip=tooltip_text,
            ).add_to(m)

    # Display the map in Streamlit
    html_str = m._repr_html_()
    html(html_str, height=600)

    fig = px.scatter(
        df_clean,  # Data to be plotted
        x="Aircraft_ID",  # X-axis data (Aircraft ID)
        y="Altitude",  # Y-axis data (Altitude)
        color="Aircraft_ID",  # Color the points based on Aircraft ID
        title="Altitude of each flight for the selected time frame",  # Title of the plot
        labels={
            "Altitude": "Altitude (ft)",
            "Aircraft_ID": "Aircraft ID",
        },  # Custom axis labels
        hover_data={
            "Altitude": True,
            "Aircraft_ID": True,
        },  # Display Aircraft ID and Altitude on hover
    )

    # Customize the legend layout
    fig.update_layout(
        legend=dict(
            title="Aircraft ID",  # Title of the legend
            orientation="v",  # Vertical orientation of the legend
            yanchor="top",  # Anchor the legend to the top
            y=1,  # Position the legend at the top of the plot (Y-axis)
            xanchor="left",  # Anchor the legend to the left of the plot
            x=1.02,  # Offset the legend slightly outside the plot
            font=dict(
                size=12,  # Set font size for the legend
            ),
        ),
        width=800,  # Set the width of the plot
        height=500,  # Set the height of the plot
    )

    # Add interactivity to highlight selected elements
    fig.update_traces(
        marker=dict(size=10, opacity=0.8),  # Customize the markers (size and opacity)
        selector=dict(mode="markers"),  # Apply these settings to marker traces
    )

    # Display the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)
