from collections import defaultdict

import altair as alt
import pandas as pd
import streamlit as st

from functions.functions1 import (
    compare_loa_separation,
    compare_radar_separation,
    compare_wake_separation,
    general,
    load_24h,
    load_flights,
)

# Streamlit page configuration
st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",  # Permite usar todo el ancho de la página
    initial_sidebar_state="expanded",
)

st.title("Separation Losses")
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
selected_time_frame = st.sidebar.selectbox(
    "Select Time Frame", list(time_frame_options.keys())
)
selected_flights = time_frame_options[selected_time_frame]

results_24L_TMA, results_06R_TMA, results_24L_TWR, results_06R_TWR, flight_info = general(selected_flights)
# Crear un defaultdict para sumar las claves comunes
combined_results_TMA = defaultdict(float)

# Sumar los valores de results_24L
for key, value in results_24L_TMA.items():
    combined_results_TMA[key] += value

# Sumar los valores de results_06R
for key, value in results_06R_TMA.items():
    combined_results_TMA[key] += value

# Convertir de nuevo a un diccionario normal si lo prefieres
combined_results_TMA = dict(combined_results_TMA)

# Crear un defaultdict para sumar las claves comunes
combined_results_TWR = defaultdict(float)

# Sumar los valores de results_24L
for key, value in results_24L_TMA.items():
    combined_results_TWR[key] += value

# Sumar los valores de results_06R
for key, value in results_06R_TMA.items():
    combined_results_TWR[key] += value

# Convertir de nuevo a un diccionario normal si lo prefieres
combined_results_TWR = dict(combined_results_TWR)

ATC_options = {
    "TMA": "tma",
    "TWR": "twr",
}
selected_ATC = st.sidebar.selectbox("Select ATC zone", list(ATC_options.keys()))
selected_ATC_results = ATC_options[selected_ATC]

# Opciones de pista con lógica para elegir los resultados correspondientes
if selected_ATC_results == "tma":
    runway_options = {
        "24L": results_24L_TMA,
        "06R": results_06R_TMA,
        "24L and 06R": combined_results_TMA,
    }
else:  # Si es TWR
    runway_options = {
        "24L": results_24L_TWR,
        "06R": results_06R_TWR,
        "24L and 06R": combined_results_TWR,
    }

selected_runway = st.sidebar.selectbox("Select Runway", list(runway_options.keys()))
selected_runway_results = runway_options[selected_runway]


st.divider()  # ===========================================================================
st.header("Radar Comparation")

# Process results
results_radar, per_radar = compare_radar_separation(selected_runway_results)

# Convert results to DataFrame
df_bars = pd.DataFrame(
    results_radar, columns=["Front Flight", "Rear Flight", "Distance (NM)", "Compliant"]
)

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
    compliance_data = pd.DataFrame(
        {
            "Category": ["Compliant", "Non-Compliant"],
            "Percentage": [per_radar, 100 - per_radar],
        }
    )

    pie_chart = (
        alt.Chart(compliance_data)
        .mark_arc()
        .encode(
            theta=alt.Theta("Percentage:Q", title="Percentage"),
            color=alt.Color(
                "Category:N", scale=alt.Scale(range=["steelblue", "orange"])
            ),
            tooltip=["Category", "Percentage"],
        )
        .properties(
            title="Compliance Percentage",
            width=300,
            height=300,
        )
    )
    st.altair_chart(pie_chart, use_container_width=True)


st.subheader("Separation Distance Between Flights")
if not df_bars.empty:
    # Bar chart
    bar_chart = (
        alt.Chart(df_bars)
        .mark_bar()
        .encode(
            x=alt.X("Rear Flight:N", title="Rear Flight"),
            y=alt.Y("Distance (NM):Q", title="Distance (NM)"),
            color=alt.condition(
                alt.datum.Compliant,
                alt.value("steelblue"),  # Compliant
                alt.value("orange"),  # Non-compliant
            ),
            tooltip=["Front Flight", "Rear Flight", "Distance (NM)", "Compliant"],
        )
        .properties(
            width=400,
            height=300,
            title="Distance Between Flights",
        )
    )

    # Add red line for threshold
    line = alt.Chart(pd.DataFrame({"y": [3]})).mark_rule(color="red").encode(y="y:Q")
    final_chart = bar_chart + line
    st.altair_chart(final_chart, use_container_width=True)
else:
    st.write("No data available for the selected filters.")

st.divider()  # ===========================================================================
st.header("Wake Comparison")

# Process results
results_wake, per_wake = compare_wake_separation(selected_runway_results, flight_info)

# Definir las separaciones mínimas para cada par de estelas
wake_separation_table = {
    ("Super Pesada", "Pesada"): 6,
    ("Super Pesada", "Media"): 7,
    ("Super Pesada", "Ligera"): 8,
    ("Pesada", "Pesada"): 4,
    ("Pesada", "Media"): 5,
    ("Pesada", "Ligera"): 6,
    ("Media", "Media"): 3,
    ("Media", "Ligera"): 5,
    ("Ligera", "Ligera"): 3,
}

# Convert results to DataFrame
df_bars = pd.DataFrame(
    results_wake,
    columns=[
        "Front Flight",
        "Rear Flight",
        "Distance (NM)",
        "Wake Class Front",
        "Wake Class Rear",
        "Min Separation",
        "Compliant",
    ],
)

# Usar st.columns para crear dos columnas ajustadas
col1, col2 = st.columns(
    2
)  # 2 columnas para las estadísticas (izquierda) y la gráfica (derecha)

with col1:
    st.subheader("Wake Class Distribution")

    # Contar cuántos aviones hay para cada tipo de estela
    wake_counts = (
        df_bars.groupby(["Wake Class Front"])
        .size()
        .reset_index(name="Number of Aircraft")
    )

    # Crear la gráfica de barras horizontal
    bar_chart = (
        alt.Chart(wake_counts)
        .mark_bar()
        .encode(
            y=alt.Y("Wake Class Front:N", title="Wake Class"),  # Estelas en el eje y
            x=alt.X(
                "Number of Aircraft:Q", title="Number of Aircraft"
            ),  # Número de aviones en el eje x
            color=alt.Color(
                "Wake Class Front:N", scale=alt.Scale(scheme="category10")
            ),  # Colores por cada clase de estela
            tooltip=[
                "Wake Class Front:N",
                "Number of Aircraft:Q",
            ],  # Mostrar los valores al pasar el mouse
        )
        .properties(
            width=500,  # Controlar el ancho
            height=300,  # Controlar la altura
            title="Number of Aircraft per Wake Class",
        )
    )

    # Mostrar la gráfica
    st.altair_chart(bar_chart, use_container_width=True)


# Columna 2: Gráfico de pastel (porcentaje de cumplimiento total)
with col2:
    st.subheader("Overall Compliance Percentage")
    compliance_data = pd.DataFrame(
        {
            "Category": ["Compliant", "Non-Compliant"],
            "Percentage": [per_wake, 100 - per_wake],
        }
    )

    pie_chart = (
        alt.Chart(compliance_data)
        .mark_arc()
        .encode(
            theta=alt.Theta("Percentage:Q", title="Percentage"),
            color=alt.Color(
                "Category:N", scale=alt.Scale(range=["steelblue", "orange"])
            ),
            tooltip=["Category", "Percentage"],
        )
        .properties(
            title="Compliance Percentage",
            width=300,  # Controlando el ancho de la gráfica
            height=300,
        )
    )

    # Mostrar la gráfica
    st.altair_chart(pie_chart, use_container_width=True)

# Asegúrate de que las columnas de estela sean de tipo string y sin espacios
df_bars["Wake Class Front"] = df_bars["Wake Class Front"].astype(str).str.strip()
df_bars["Wake Class Rear"] = df_bars["Wake Class Rear"].astype(str).str.strip()

# Crear una columna para clasificar si cumple o no con la separación mínima
df_bars["Compliance"] = df_bars["Compliant"].apply(
    lambda x: "Compliant" if x else "Non-Compliant"
)

# Filtrar el DataFrame para obtener las combinaciones de estelas
unique_wake_combinations = df_bars[
    ["Wake Class Front", "Wake Class Rear"]
].drop_duplicates()

# Establecer las columnas para mostrar las estadísticas, la gráfica y el gráfico circular
for _, row in unique_wake_combinations.iterrows():
    wake_front = row["Wake Class Front"]
    wake_rear = row["Wake Class Rear"]

    # Obtener la distancia mínima para esta combinación de estelas
    min_distance = wake_separation_table.get((wake_front, wake_rear), None)

    # Solo mostrar la gráfica si existe una distancia mínima definida
    if min_distance is not None:
        # Filtrar los datos para esa combinación específica
        subset_data = df_bars[
            (df_bars["Wake Class Front"] == wake_front)
            & (df_bars["Wake Class Rear"] == wake_rear)
        ]

        if not subset_data.empty:
            col1, col2, col3 = st.columns(
                3
            )  # Crear tres columnas para las estadísticas (izquierda), la gráfica (centro) y la gráfica circular (derecha)

            with (
                col1
            ):  # Mostrar estadísticas de distancia de separación (a la izquierda)
                st.subheader(
                    f"Statistics for Distance Between Flights: {wake_front} → {wake_rear}"
                )

                # Agrupar por Wake Class Front y Wake Class Rear
                group_stats = (
                    subset_data.groupby(["Wake Class Front", "Wake Class Rear"])
                    .agg(
                        mean_distance=("Distance (NM)", "mean"),
                        std_distance=("Distance (NM)", "std"),
                        median_distance=("Distance (NM)", "median"),
                        count=("Distance (NM)", "size"),
                    )
                    .reset_index()
                )

                # Mostrar estadísticas solo si hay datos
                if not group_stats.empty:
                    for _, stat_row in group_stats.iterrows():
                        col4, col5 = st.columns(2)
                        with col4:
                            st.metric(
                                "Mean (Average)", f"{stat_row['mean_distance']:.2f} NM"
                            )
                            st.metric(
                                "Standard Deviation",
                                f"{stat_row['std_distance']:.2f} NM",
                            )
                        with col5:
                            st.metric("Median", f"{stat_row['median_distance']:.2f} NM")
                            st.metric("Count", f"{stat_row['count']} pairs")
                else:
                    st.write("No data available for statistics.")

            with col2:  # Mostrar gráfica de separación de distancias (a la izquierda)
                st.subheader("Separation Distance")

                # Gráfico de barras
                bar_chart = (
                    alt.Chart(subset_data)
                    .mark_bar()
                    .encode(
                        x=alt.X("Rear Flight:N", title="Rear Flight"),
                        y=alt.Y("Distance (NM):Q", title="Distance (NM)"),
                        color=alt.condition(
                            alt.datum.Compliant,
                            alt.value("steelblue"),  # Compliant
                            alt.value("orange"),  # Non-compliant
                        ),
                        tooltip=[
                            "Front Flight",
                            "Rear Flight",
                            "Distance (NM)",
                            "Compliant",
                        ],
                    )
                    .properties(
                        width=400,
                        height=300,
                        title=f"Distance Between Flights ({wake_front} → {wake_rear})",
                    )
                )

                # Añadir línea roja para la distancia mínima
                line = (
                    alt.Chart(pd.DataFrame({"y": [min_distance]}))
                    .mark_rule(color="red")
                    .encode(y="y:Q")
                )
                final_chart = bar_chart + line
                st.altair_chart(final_chart, use_container_width=True)

            with (
                col3
            ):  # Mostrar gráfico circular con el porcentaje de aviones que cumplen y los que no
                st.subheader("Compliance Percentage")

                # Verificar si la columna 'Compliant' contiene valores válidos
                if (
                    subset_data["Compliant"].notna().any()
                ):  # Verifica si hay valores no nulos
                    # Calcular los porcentajes de aviones Compliant y Non-Compliant
                    compliance_counts = (
                        subset_data["Compliant"].value_counts(normalize=True) * 100
                    )

                    if (
                        not compliance_counts.empty
                    ):  # Verificar si hay valores en compliance_counts
                        compliance_data = pd.DataFrame(
                            {
                                "Category": compliance_counts.index.astype(
                                    str
                                ),  # Asegurarse de que los índices sean cadenas para el gráfico
                                "Percentage": compliance_counts.values,
                            }
                        )

                        # Gráfico circular (pie chart)
                        pie_chart = (
                            alt.Chart(compliance_data)
                            .mark_arc()
                            .encode(
                                theta=alt.Theta("Percentage:Q", title="Percentage"),
                                color=alt.Color(
                                    "Category:N",
                                    scale=alt.Scale(
                                        domain=["True", "False"],
                                        range=["steelblue", "orange"],
                                    ),
                                    title="Compliance",
                                ),
                                tooltip=["Category", "Percentage"],
                            )
                            .properties(
                                title="Compliance Percentage", width=300, height=300
                            )
                        )

                        st.altair_chart(pie_chart, use_container_width=True)
                    else:
                        st.write("No compliance data available.")
                else:
                    st.write("No valid compliance data available.")


if selected_ATC_results == "twr":

    st.divider()  # ===========================================================================
    st.header("LoA Comparison")

    # Process results
    results_loa, per_loa = compare_loa_separation(selected_runway_results, flight_info)

    # Convertir los resultados en un DataFrame
    df_bars = pd.DataFrame(
        results_loa,
        columns=[
            "Front Flight",
            "Rear Flight",
            "Distance (NM)",
            "Category Front",
            "Category Rear",
            "Min Separation",
            "Same SID",
            "Group Rear",
            "Compliant",
        ],
    )

    # Limpiar las columnas de categoría
    df_bars["Category Front"] = df_bars["Category Front"].astype(str).str.strip()
    df_bars["Category Rear"] = df_bars["Category Rear"].astype(str).str.strip()

    # Crear una columna de cumplimiento (texto) para gráficos y visualizaciones
    df_bars["Compliance"] = df_bars["Compliant"].apply(
        lambda x: "Compliant" if x else "Non-Compliant"
    )

    # Crear columnas para los gráficos
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Number of Aircraft by Type")

        # Crear un DataFrame con el conteo de aviones por tipo de aeronave en 'Category Front'
        aircraft_type_counts = (
            df_bars.groupby(["Category Front"])
            .size()
            .reset_index(name="Number of Aircraft")
        )

        # Crear gráfico de barras utilizando 'Category Front'
        bar_chart_aircraft_type = (
            alt.Chart(aircraft_type_counts)
            .mark_bar()
            .encode(
                y=alt.Y(
                    "Category Front:N", title="Category Front", sort="-x"
                ),  # Eje Y: 'Category Front'
                x=alt.X(
                    "Number of Aircraft:Q", title="Number of Aircraft"
                ),  # Eje X: 'Number of Aircraft'
                color=alt.Color(
                    "Category Front:N", scale=alt.Scale(scheme="category10")
                ),  # Colores por 'Category Front'
                tooltip=[
                    "Category Front:N",
                    "Number of Aircraft:Q",
                ],  # Información en el tooltip
            )
            .properties(
                width=500,  # Ancho del gráfico
                height=300,  # Alto del gráfico
                title="Aircraft Count by Type",  # Título del gráfico
            )
        )

        st.altair_chart(bar_chart_aircraft_type, use_container_width=True)


    with col2:
        st.subheader("Overall Compliance Percentage")
        compliance_data = pd.DataFrame(
            {
                "Category": ["Compliant", "Non-Compliant"],
                "Percentage": [per_loa, 100 - per_loa],
            }
        )

        pie_chart = (
            alt.Chart(compliance_data)
            .mark_arc()
            .encode(
                theta=alt.Theta("Percentage:Q", title="Percentage"),
                color=alt.Color(
                    "Category:N", scale=alt.Scale(range=["steelblue", "orange"])
                ),
                tooltip=["Category", "Percentage"],
            )
            .properties(
                title="Compliance Percentage",
                width=300,
                height=300,
            )
        )
        st.altair_chart(pie_chart, use_container_width=True)


    loa_separation = {
        ("HP", "HP", "Misma"): 5,
        ("HP", "HP", "Distinta"): 3,
        ("HP", "R", "Misma"): 5,
        ("HP", "R", "Distinta"): 3,
        ("HP", "LP", "Misma"): 5,
        ("HP", "LP", "Distinta"): 3,
        ("HP", "NR+", "Misma"): 3,
        ("HP", "NR+", "Distinta"): 3,
        ("HP", "NR-", "Misma"): 3,
        ("HP", "NR-", "Distinta"): 3,
        ("HP", "NR", "Misma"): 3,
        ("HP", "NR", "Distinta"): 3,
        ("R", "HP", "Misma"): 7,
        ("R", "HP", "Distinta"): 5,
        ("R", "R", "Misma"): 5,
        ("R", "R", "Distinta"): 3,
        ("R", "LP", "Misma"): 5,
        ("R", "LP", "Distinta"): 3,
        ("R", "NR+", "Misma"): 3,
        ("R", "NR+", "Distinta"): 3,
        ("R", "NR-", "Misma"): 3,
        ("R", "NR-", "Distinta"): 3,
        ("R", "NR", "Misma"): 3,
        ("R", "NR", "Distinta"): 3,
        ("LP", "HP", "Misma"): 8,
        ("LP", "HP", "Distinta"): 6,
        ("LP", "R", "Misma"): 6,
        ("LP", "R", "Distinta"): 4,
        ("LP", "LP", "Misma"): 5,
        ("LP", "LP", "Distinta"): 3,
        ("LP", "NR+", "Misma"): 3,
        ("LP", "NR+", "Distinta"): 3,
        ("LP", "NR-", "Misma"): 3,
        ("LP", "NR-", "Distinta"): 3,
        ("LP", "NR", "Misma"): 3,
        ("LP", "NR", "Distinta"): 3,
        ("NR+", "HP", "Misma"): 11,
        ("NR+", "HP", "Distinta"): 8,
        ("NR+", "R", "Misma"): 9,
        ("NR+", "R", "Distinta"): 6,
        ("NR+", "LP", "Misma"): 9,
        ("NR+", "LP", "Distinta"): 6,
        ("NR+", "NR+", "Misma"): 5,
        ("NR+", "NR+", "Distinta"): 3,
        ("NR+", "NR-", "Misma"): 3,
        ("NR+", "NR-", "Distinta"): 3,
        ("NR+", "NR", "Misma"): 3,
        ("NR+", "NR", "Distinta"): 3,
        ("NR-", "HP", "Misma"): 9,
        ("NR-", "HP", "Distinta"): 9,
        ("NR-", "R", "Misma"): 9,
        ("NR-", "R", "Distinta"): 9,
        ("NR-", "LP", "Misma"): 9,
        ("NR-", "LP", "Distinta"): 9,
        ("NR-", "NR+", "Misma"): 9,
        ("NR-", "NR+", "Distinta"): 6,
        ("NR-", "NR-", "Misma"): 5,
        ("NR-", "NR-", "Distinta"): 3,
        ("NR-", "NR", "Misma"): 3,
        ("NR-", "NR", "Distinta"): 3,
        ("NR", "HP", "Misma"): 9,
        ("NR", "HP", "Distinta"): 9,
        ("NR", "R", "Misma"): 9,
        ("NR", "R", "Distinta"): 9,
        ("NR", "LP", "Misma"): 9,
        ("NR", "LP", "Distinta"): 9,
        ("NR", "NR+", "Misma"): 9,
        ("NR", "NR+", "Distinta"): 9,
        ("NR", "NR-", "Misma"): 9,
        ("NR", "NR-", "Distinta"): 9,
        ("NR", "NR", "Misma"): 5,
        ("NR", "NR", "Distinta"): 3,
    }

    # Iterar por cada combinación de categorías y condiciones
    for (front_category, rear_category, condition), min_distance in loa_separation.items():
        # Filtrar los datos para esta combinación
        subset_data = df_bars[
            (df_bars["Category Front"] == front_category)
            & (df_bars["Category Rear"] == rear_category)
            & (
                df_bars["Same SID"] == condition
            )  # Cambia esto por la columna correspondiente
        ]

        # Proceder si hay datos para esta combinación
        if not subset_data.empty:
            st.subheader(f"Combination: {front_category} → {rear_category} ({condition})")

            # Crear columnas para estadísticas, gráfica de barras y gráfica circular
            col1, col2, col3 = st.columns(3)

            with col1:  # Mostrar estadísticas de distancia de separación (a la izquierda)
                st.subheader(
                    f"Statistics for Distance Between Flights: {front_category} → {rear_category}"
                )

                # Agrupar por las columnas relevantes (categorías front y rear)
                group_stats = (
                    subset_data.groupby(["Category Front", "Category Rear"])
                    .agg(
                        mean_distance=("Distance (NM)", "mean"),
                        std_distance=("Distance (NM)", "std"),
                        median_distance=("Distance (NM)", "median"),
                        count=("Distance (NM)", "size"),
                    )
                    .reset_index()
                )

                # Mostrar estadísticas solo si hay datos
                if not group_stats.empty:
                    for _, stat_row in group_stats.iterrows():
                        col4, col5 = st.columns(
                            2
                        )  # Dividir las métricas en dos columnas para mejor visualización
                        with col4:
                            st.metric(
                                "Mean (Average)", f"{stat_row['mean_distance']:.2f} NM"
                            )
                            st.metric(
                                "Standard Deviation", f"{stat_row['std_distance']:.2f} NM"
                            )
                        with col5:
                            st.metric("Median", f"{stat_row['median_distance']:.2f} NM")
                            st.metric("Count", f"{stat_row['count']} pairs")
                else:
                    st.write("No data available for statistics.")

            # Gráfica de barras para distancias de separación
            with col2:
                st.subheader("Separation Distance Distribution")
                bar_chart = (
                    alt.Chart(subset_data)
                    .mark_bar()
                    .encode(
                        x=alt.X("Rear Flight:N", title="Rear Flight"),
                        y=alt.Y("Distance (NM):Q", title="Distance (NM)"),
                        color=alt.condition(
                            alt.datum.Compliant,
                            alt.value("steelblue"),  # Compliant
                            alt.value("orange"),  # Non-compliant
                        ),
                        tooltip=[
                            "Front Flight",
                            "Rear Flight",
                            "Distance (NM)",
                            "Compliant",
                        ],
                    )
                    .properties(
                        width=400,
                        height=300,
                        title=f"Distance Between Flights ({front_category} → {rear_category})",
                    )
                )

                # Añadir una línea roja para la distancia mínima
                line = (
                    alt.Chart(pd.DataFrame({"y": [min_distance]}))
                    .mark_rule(color="red")
                    .encode(y="y:Q")
                )
                final_chart = bar_chart + line
                st.altair_chart(final_chart, use_container_width=True)

            # Gráfica circular para porcentaje de cumplimiento
            with col3:
                st.subheader("Compliance Percentage")
                compliance_counts = (
                    subset_data["Compliant"].value_counts(normalize=True) * 100
                )
                compliance_data = pd.DataFrame(
                    {
                        "Category": [
                            "Compliant" if k else "Non-Compliant"
                            for k in compliance_counts.index
                        ],
                        "Percentage": compliance_counts.values,
                    }
                )

                if not compliance_data.empty:
                    pie_chart = (
                        alt.Chart(compliance_data)
                        .mark_arc()
                        .encode(
                            theta=alt.Theta("Percentage:Q", title="Percentage"),
                            color=alt.Color(
                                "Category:N",
                                scale=alt.Scale(
                                    domain=["Compliant", "Non-Compliant"],
                                    range=["steelblue", "orange"],
                                ),
                            ),
                            tooltip=["Category", "Percentage"],
                        )
                        .properties(title="Compliance Percentage", width=300, height=300)
                    )
                    st.altair_chart(pie_chart, use_container_width=True)
                else:
                    st.write("No compliance data available.")


    # Estadísticas por grupos de SIDs
    sid_counts = (
        df_bars.groupby(["Group Rear"]).size().reset_index(name="Number of Aircraft")
    )
    sid_compliance = (
        df_bars.groupby(["Group Rear", "Compliance"])
        .size()
        .reset_index(name="Count")
        .pivot(index="Group Rear", columns="Compliance", values="Count")
        .fillna(0)
        .reset_index()
    )

    # Intentar realizar el cálculo de la columna de cumplimiento
    try:
        sid_compliance["Total"] = (
            sid_compliance["Compliant"] + sid_compliance["Non-Compliant"]
        )
        sid_compliance["Compliance (%)"] = (
            sid_compliance["Compliant"] / sid_compliance["Total"]
        ) * 100
        sid_compliance["Non-Compliance (%)"] = (
            sid_compliance["Non-Compliant"] / sid_compliance["Total"]
        ) * 100

        # Crear columnas para los gráficos
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Number of Aircraft by SID Group")
            bar_chart_sids = (
                alt.Chart(sid_counts)
                .mark_bar()
                .encode(
                    y=alt.Y("Group Rear:N", title="SID Group", sort="-x"),
                    x=alt.X("Number of Aircraft:Q", title="Number of Aircraft"),
                    color=alt.Color("Group Rear:N", scale=alt.Scale(scheme="category10")),
                    tooltip=["Group Rear:N", "Number of Aircraft:Q"],
                )
                .properties(width=500, height=300, title="Aircraft Count by SID Group")
            )
            st.altair_chart(bar_chart_sids, use_container_width=True)

        with col2:
            # Gráfico de cumplimiento por SID Group
            st.subheader("Compliance Distribution by SID Group")
            sid_compliance_melted = sid_compliance.melt(
                id_vars="Group Rear",
                value_vars=["Compliance (%)", "Non-Compliance (%)"],
                var_name="Compliance Type",
                value_name="Percentage",
            )
            sid_group_chart = (
                alt.Chart(sid_compliance_melted)
                .mark_bar()
                .encode(
                    x=alt.X("Percentage:Q", title="Percentage"),
                    y=alt.Y("Group Rear:N", title="SID Group", sort="-x"),
                    color=alt.Color(
                        "Compliance Type:N", scale=alt.Scale(range=["steelblue", "orange"])
                    ),
                    tooltip=["Group Rear:N", "Compliance Type:N", "Percentage:Q"],
                )
                .properties(
                    width=500, height=300, title="Compliance Percentage by SID Group"
                )
            )
            st.altair_chart(sid_group_chart, use_container_width=True)

    except Exception:
        st.write("No data available for SID groups.")
