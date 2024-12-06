import streamlit as st
import altair as alt
import pandas as pd
from functions.functions1 import load_flights, load_24h, general, compare_radar_separation, compare_wake_separation, compare_loa_separation


# Streamlit page configuration
st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("ATM Project - Separation Losses")
st.write("Here you can see the distance between flights when taking off")
st.write("You can filter by Radar, Wake or LoA")

# Load data
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

results_24L, results_06R, flight_info = general(selected_flights)

#results = results_24L+results_06R

runway_options = {
    "24L": results_24L,
    "06R": results_06R,
    #"24L and 06R": results
}
selected_runway = st.selectbox("Select Runway", list(runway_options.keys()))
selected_runway_results = runway_options[selected_runway]

results_radar, per_radar = compare_radar_separation(selected_runway_results)
results_wake, per_wake = compare_wake_separation(selected_runway_results, flight_info)
results_loa, per_loa = compare_loa_separation(selected_runway_results, flight_info)

# Convertir los resultados en un DataFrame
df_bars = pd.DataFrame(results_radar, columns=["Front Flight", "Rear Flight", "Distance (NM)", "Compliant"])

# Gráfico de barras
bar_chart = alt.Chart(df_bars).mark_bar().encode(
    x=alt.X("Rear Flight:N", title="Rear Flight"),  # Eje X: vuelos traseros
    y=alt.Y("Distance (NM):Q", title="Distance (NM)"),  # Eje Y: distancias en millas náuticas
    color=alt.condition(
        alt.datum["Compliant"],  # Colorear según cumplimiento
        alt.value("steelblue"),  # Cumple: azul
        alt.value("orange"),  # No cumple: naranja
    ),
    tooltip=["Front Flight", "Rear Flight", "Distance (NM)", "Compliant"]  # Tooltip con detalles
).properties(
    width=800,
    height=400,
    title="Separation Distance Between Flights"
)

# Línea roja en Y=3
line = alt.Chart(pd.DataFrame({"y": [3]})).mark_rule(color="red").encode(
    y="y:Q"
)

# Combinar gráfico de barras con línea roja
final_chart = bar_chart + line

# Mostrar en Streamlit
st.altair_chart(final_chart, use_container_width=True)

# Crear gráfica circular con porcentaje de cumplimiento
compliance_data = pd.DataFrame({
    "Category": ["Compliant", "Non-Compliant"],
    "Percentage": [per_radar, 100 - per_radar],
})

pie_chart = alt.Chart(compliance_data).mark_arc().encode(
    theta=alt.Theta("Percentage:Q", title="Percentage"),
    color=alt.Color("Category:N", title="Category", scale=alt.Scale(range=["steelblue", "orange"])),
    tooltip=["Category", "Percentage"]
).properties(
    title="Compliance Percentage"
)

# Mostrar gráfica circular en Streamlit
st.altair_chart(pie_chart, use_container_width=True)

# Calcular estadísticas
st.subheader("Statistics for Distance Between Flights")
if not df_bars.empty:
    mean_distance = df_bars["Distance (NM)"].mean()
    std_distance = df_bars["Distance (NM)"].std()
    median_distance = df_bars["Distance (NM)"].median()
    
    st.write(f"**Mean (Average):** {mean_distance:.2f} NM")
    st.write(f"**Standard Deviation:** {std_distance:.2f} NM")
    st.write(f"**Median:** {median_distance:.2f} NM")
else:
    st.write("No data available for the selected runway and time frame.")
