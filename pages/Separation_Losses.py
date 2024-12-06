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

st.divider()#===========================================================================
st.header("Radar Comparation")

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

st.divider() #===========================================================================
st.header("Wake Comparison")

# Definir las separaciones mínimas para cada par de estelas
wake_separation_table = {
    ('Super Pesada', 'Pesada'): 6,
    ('Super Pesada', 'Media'): 7,
    ('Super Pesada', 'Ligera'): 8,
    ('Pesada', 'Pesada'): 4,
    ('Pesada', 'Media'): 5,
    ('Pesada', 'Ligera'): 6,
    ('Media', 'Media'): 3,
    ('Media', 'Ligera'): 5,
    ('Ligera', 'Ligera'): 3
}

# Process results
results_wake, per_wake = compare_wake_separation(selected_runway_results, flight_info)

# Convert results to DataFrame
df_bars = pd.DataFrame(results_wake, columns=["Front Flight", "Rear Flight", "Distance (NM)", "Wake Class Front", "Wake Class Rear", "Min Separation", "Compliant"])

# Usar st.columns para crear dos columnas ajustadas
col1, col2 = st.columns(2)  # 2 columnas para las estadísticas (izquierda) y la gráfica (derecha)

with col1:
    st.subheader("Wake Class Distribution")

    # Contar cuántos aviones hay para cada tipo de estela
    wake_counts = df_bars.groupby(['Wake Class Front']).size().reset_index(name='Number of Aircraft')

    # Crear la gráfica de barras horizontal
    bar_chart = alt.Chart(wake_counts).mark_bar().encode(
        y=alt.Y("Wake Class Front:N", title="Wake Class"),  # Estelas en el eje y
        x=alt.X("Number of Aircraft:Q", title="Number of Aircraft"),  # Número de aviones en el eje x
        color=alt.Color("Wake Class Front:N", scale=alt.Scale(scheme="category10")),  # Colores por cada clase de estela
        tooltip=["Wake Class Front:N", "Number of Aircraft:Q"]  # Mostrar los valores al pasar el mouse
    ).properties(
        width=500,  # Controlar el ancho
        height=300,  # Controlar la altura
        title="Number of Aircraft per Wake Class"
    )

    # Mostrar la gráfica
    st.altair_chart(bar_chart, use_container_width=True)


# Columna 2: Gráfico de pastel (porcentaje de cumplimiento total)
with col2:
    st.subheader("Overall Compliance Percentage")
    compliance_data = pd.DataFrame({
        "Category": ["Compliant", "Non-Compliant"],
        "Percentage": [per_wake, 100 - per_wake],
    })

    pie_chart = alt.Chart(compliance_data).mark_arc().encode(
        theta=alt.Theta("Percentage:Q", title="Percentage"),
        color=alt.Color("Category:N", scale=alt.Scale(range=["steelblue", "orange"])),
        tooltip=["Category", "Percentage"],
    ).properties(
        title="Compliance Percentage",
        width=300,  # Controlando el ancho de la gráfica
        height=300,
    )

    # Mostrar la gráfica
    st.altair_chart(pie_chart, use_container_width=True)

# Asegúrate de que las columnas de estela sean de tipo string y sin espacios
df_bars['Wake Class Front'] = df_bars['Wake Class Front'].astype(str).str.strip()
df_bars['Wake Class Rear'] = df_bars['Wake Class Rear'].astype(str).str.strip()

# Crear una columna para clasificar si cumple o no con la separación mínima
df_bars['Compliance'] = df_bars['Compliant'].apply(lambda x: 'Compliant' if x else 'Non-Compliant')

# Filtrar el DataFrame para obtener las combinaciones de estelas
unique_wake_combinations = df_bars[['Wake Class Front', 'Wake Class Rear']].drop_duplicates()

# Establecer las columnas para mostrar las estadísticas, la gráfica y el gráfico circular
for _, row in unique_wake_combinations.iterrows():
    wake_front = row['Wake Class Front']
    wake_rear = row['Wake Class Rear']
    
    # Obtener la distancia mínima para esta combinación de estelas
    min_distance = wake_separation_table.get((wake_front, wake_rear), None)
    
    # Solo mostrar la gráfica si existe una distancia mínima definida
    if min_distance is not None:
        # Filtrar los datos para esa combinación específica
        subset_data = df_bars[(df_bars['Wake Class Front'] == wake_front) & (df_bars['Wake Class Rear'] == wake_rear)]
        
        if not subset_data.empty:
            col1, col2, col3 = st.columns(3)  # Crear tres columnas para las estadísticas (izquierda), la gráfica (centro) y la gráfica circular (derecha)
            
            with col1:  # Mostrar estadísticas de distancia de separación (a la izquierda)
                st.subheader(f"Statistics for Distance Between Flights: {wake_front} → {wake_rear}")
                
                # Agrupar por Wake Class Front y Wake Class Rear
                group_stats = subset_data.groupby(["Wake Class Front", "Wake Class Rear"]).agg(
                    mean_distance=("Distance (NM)", "mean"),
                    std_distance=("Distance (NM)", "std"),
                    median_distance=("Distance (NM)", "median"),
                    count=("Distance (NM)", "size")
                ).reset_index()

                # Mostrar estadísticas solo si hay datos
                if not group_stats.empty:
                    for _, stat_row in group_stats.iterrows():
                        col4, col5 = st.columns(2)
                        with col4:
                            st.metric("Mean (Average)", f"{stat_row['mean_distance']:.2f} NM")
                            st.metric("Standard Deviation", f"{stat_row['std_distance']:.2f} NM")
                        with col5:
                            st.metric("Median", f"{stat_row['median_distance']:.2f} NM")
                            st.metric("Count", f"{stat_row['count']} pairs")
                else:
                    st.write("No data available for statistics.")
            
            with col2:  # Mostrar gráfica de separación de distancias (a la izquierda)
                st.subheader(f"Separation Distance")
                
                # Gráfico de barras
                bar_chart = alt.Chart(subset_data).mark_bar().encode(
                    x=alt.X("Rear Flight:N", title="Rear Flight"),
                    y=alt.Y("Distance (NM):Q", title="Distance (NM)"),
                    color=alt.condition(
                        alt.datum.Compliant,
                        alt.value("steelblue"),  # Compliant
                        alt.value("orange"),  # Non-compliant
                    ),
                    tooltip=["Front Flight", "Rear Flight", "Distance (NM)", "Compliant"]
                ).properties(
                    width=400,
                    height=300,
                    title=f"Distance Between Flights ({wake_front} → {wake_rear})"
                )
                
                # Añadir línea roja para la distancia mínima
                line = alt.Chart(pd.DataFrame({"y": [min_distance]})).mark_rule(color="red").encode(y="y:Q")
                final_chart = bar_chart + line
                st.altair_chart(final_chart, use_container_width=True)

            with col3:  # Mostrar gráfico circular con el porcentaje de aviones que cumplen y los que no
                st.subheader("Compliance Percentage")

                # Verificar si la columna 'Compliant' contiene valores válidos
                if subset_data['Compliant'].notna().any():  # Verifica si hay valores no nulos
                    # Calcular los porcentajes de aviones Compliant y Non-Compliant
                    compliance_counts = subset_data['Compliant'].value_counts(normalize=True) * 100
                    
                    if not compliance_counts.empty:  # Verificar si hay valores en compliance_counts
                        compliance_data = pd.DataFrame({
                            "Category": compliance_counts.index.astype(str),  # Asegurarse de que los índices sean cadenas para el gráfico
                            "Percentage": compliance_counts.values
                        })

                        # Gráfico circular (pie chart)
                        pie_chart = alt.Chart(compliance_data).mark_arc().encode(
                            theta=alt.Theta("Percentage:Q", title="Percentage"),
                            color=alt.Color("Category:N", scale=alt.Scale(domain=['True', 'False'], range=["steelblue", "orange"]), title="Compliance"),
                            tooltip=["Category", "Percentage"]
                        ).properties(
                            title="Compliance Percentage",
                            width=300,
                            height=300
                        )

                        st.altair_chart(pie_chart, use_container_width=True)
                    else:
                        st.write("No compliance data available.")
                else:
                    st.write("No valid compliance data available.")

st.divider()#===========================================================================
st.header("LoA Comparation")
