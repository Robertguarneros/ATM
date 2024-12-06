import matplotlib.pyplot as plt
import altair as alt
import streamlit as st
import pandas as pd
import plotly.express as px
from functions.functions2 import load_flights, load_departures, load_24h, extract_IAS

# Streamlit page configuration
st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("IAS data")
st.write("Here we can see the IAS of departures at 850, 1500 and 3500 ft for both runways")

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

ias_06R, ias_24L = (extract_IAS(loaded_departures, selected_flights))

runway_options = {
    "24L": ias_24L,
    "06R": ias_06R,
    "24L and 06R": ias_24L, 
}

selected_runway = st.sidebar.selectbox("Select Runway", list(runway_options.keys()))
selected_runway_results = runway_options[selected_runway]

data = []

# Si el usuario selecciona "24L and 06R", manejamos ambos conjuntos de datos
if selected_runway == "24L and 06R":
    # Agregar datos de 24L
    for altitude, values in ias_24L.items():
        for aircraft_id, ias in values:
            data.append({'Runway': '24L', 'Altitude': altitude, 'IAS': ias, 'Aircraft_ID': aircraft_id})
    # Agregar datos de 06R
    for altitude, values in ias_06R.items():
        for aircraft_id, ias in values:
            data.append({'Runway': '06R', 'Altitude': altitude, 'IAS': ias, 'Aircraft_ID': aircraft_id})
else:
    # Si solo seleccionan 06R o 24L, procesamos solo esa pista
    for altitude, values in selected_runway_results.items():
        for aircraft_id, ias in values:
            data.append({'Runway': selected_runway, 'Altitude': altitude, 'IAS': ias, 'Aircraft_ID': aircraft_id})

df = pd.DataFrame(data)

if df.empty:
    st.warning(f"No departures for Runway {selected_runway} during this period.")
else:
    filtered_df = df[df['Altitude'].isin([850,1500,3500])]

    st.subheader("Summary Statistics")
    
    for altitude in [850, 1500, 3500]:

        altitude_data = filtered_df[(filtered_df['Altitude'] == altitude)]

        cols = st.columns([1.5, 2, 2, 2, 2])  # Proporciones de las columnas, la columna 0 es más pequeña, las demás son más grandes.
        cols[0].markdown('<br>', unsafe_allow_html=True) # Adds vertical space to "center" the text vertically
        cols[0].markdown(f"#####   {altitude} ft")
            
        cols[1].metric("Mean IAS (knots)", f"{altitude_data['IAS'].mean():.2f}")
        cols[2].metric("Median IAS (knots)", f"{altitude_data['IAS'].median():.2f}")
        
        # Safely get the mode for Runway 06R
        mode = altitude_data['IAS'].mode()
        mode_value = mode.iloc[0] if not mode.empty else "nan"
            
        # Create space for centering the metric and print mode
        cols[3].metric("Mode IAS (knots)", f"{mode_value:.2f}" if mode_value != "nan" else mode_value)
        cols[4].metric("Std. Deviation (knots)", f"{altitude_data['IAS'].std():.2f}")
    
    st.divider()  # Add a visual divider between sections

    ias_bins = [(90, 120), (120, 150), (150, 180), (180, 210), (210, 240), (240, 270)]
    bin_labels = ["90-120kt", "120-150kt", "150-180kt", "180-210kt", "210-240kt", "240-270kt"]

    def get_ias_range(ias):
        for i, (low, high) in enumerate(ias_bins):
            if low <= ias < high:
                return bin_labels[i]
        return "Unknown"

    # Crear la columna IAS_Range si no existe
    filtered_df["IAS_Range"] = filtered_df["IAS"].apply(get_ias_range)

    ias_distribution_total = (
        filtered_df.groupby("IAS_Range")
        .size()
        .reset_index(name="Count")
    )

    # Ajustar el gráfico con datos limpios y agrupados por rango
    st.subheader("Distribution of IAS")

    col1, col2 = st.columns(2)

    with col1:
        range_counts = filtered_df["IAS_Range"].value_counts(normalize=True).reset_index()
        range_counts.columns = ["Range", "Percentage"]
        range_counts["Percentage"] *= 100  # Convert to percenta
        st.altair_chart(
            alt.Chart(range_counts).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("Percentage:Q", title="Percentage of Flights"),
                color=alt.Color("Range:N", title="IAS Range"),
                tooltip=["Range:N", "Percentage:Q"]
            ).properties(
                title="Distribution of IAS by Range",
                width=400,
                height=400
            ),
            use_container_width=True
        )

    # Boxplot of IAS by Runway and Altitude
    with col2:
        st.altair_chart(
            alt.Chart(df).mark_boxplot().encode(
                x="Altitude:N",
                y=alt.Y("IAS:Q", scale=alt.Scale(zero=False)),
                color="Runway:N"
            ).properties(
                title="IAS Distribution by  Altitude",
                width=400,
                height=400
            ),
            use_container_width=True
        )

    st.divider()  # Another divider

    # Line chart for IAS evolution
    st.subheader(f"IAS of each flight from({selected_time_frame})")

    # Create an interactive plot with Plotly
    fig = px.scatter(
        filtered_df,  # Data to be plotted
        x="Altitude",  # X-axis data (Altitude)
        y="IAS",  # Y-axis data (Indicated Airspeed)
        color="Aircraft_ID",  # Color the points based on Aircraft ID
        title=f"IAS of each flight for runway {selected_runway}",  # Title of the plot
        labels={"Altitude": "Altitude (ft)", "IAS": "IAS (knots)"},  # Custom axis labels
        category_orders={"Altitude": [850, 1500, 3500]},  # Define the domain for the X-axis
        hover_data={"Altitude": False, "IAS": True, "Aircraft_ID": True}  # Control the hover data display
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
            )
        ),
        width=800,  # Set the width of the plot
        height=600  # Set the height of the plot
    )

    # Add interactivity to highlight selected elements
    fig.update_traces(
        marker=dict(size=10, opacity=0.8),  # Customize the markers (size and opacity)
        selector=dict(mode='markers')  # Apply these settings to marker traces
    )

    # Display the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)  # Ensure the plot uses the full width of the container
