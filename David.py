# Son los q me ha dicho GPT si hay otros mejores se cambia
import tkinter as tk
from datetime import timedelta
from tkinter import filedialog

import pandas as pd


def extract_contiguous_pairs():
    # Cargar el archivo
    file_path = "assets/InputFiles/2305_02_dep_lebl.xlsx"
    df = pd.read_excel(file_path)

    time_threshold_minutes = 4

    # Convertir la columna 'HoraDespegue' a tipo datetime
    df["HoraDespegue"] = pd.to_datetime(df["HoraDespegue"])

    # Ordenar por 'HoraDespegue'
    df_sorted = df.sort_values(by="HoraDespegue").reset_index(drop=True)

    # Listas para almacenar los vuelos contiguos por pista
    contiguous_flights_24L = []
    contiguous_flights_06R = []

    # Iterar sobre las filas para calcular diferencias entre vuelos consecutivos
    for i in range(len(df_sorted) - 1):
        current_flight = df_sorted.iloc[i]
        next_flight = df_sorted.iloc[i + 1]

        # Calcular la diferencia de tiempo entre vuelos consecutivos
        time_difference = next_flight["HoraDespegue"] - current_flight["HoraDespegue"]

        if time_difference < timedelta(minutes=time_threshold_minutes):
            # Verificar la pista de despegue y añadir al grupo correspondiente
            if (
                current_flight.iloc[7] == "LEBL-24L"
                and next_flight.iloc[7] == "LEBL-24L"
            ):
                contiguous_flights_24L.append(
                    (current_flight["Indicativo"], next_flight["Indicativo"])
                )
            elif (
                current_flight.iloc[7] == "LEBL-06R"
                and next_flight.iloc[7] == "LEBL-06R"
            ):
                contiguous_flights_06R.append(
                    (current_flight["Indicativo"], next_flight["Indicativo"])
                )

    return contiguous_flights_24L, contiguous_flights_06R


pairs_24L, pairs_06R = extract_contiguous_pairs()
print("Contiguous flights for LEBL-24L:", pairs_24L)
print("Contiguous flights for LEBL-06R:", pairs_06R)


"""

# Función para seleccionar el archivo CSV
def select_file():
    root = tk.Tk()  # Crear una ventana raíz
    root.withdraw()  # Ocultar la ventana raíz
    file_path = filedialog.askopenfilename(title="Selecciona un archivo CSV", filetypes=[("CSV files", "*.csv")])  # Abrir el cuadro de diálogo
    return file_path


# Llamada a la función para seleccionar el archivo
#file_path = select_file()


def extract_contiguous_pairs(file_path):
    # Leer el archivo con el delimitador adecuado y manejar valores nulos
    df = pd.read_csv(file_path, sep=';', na_values=['N/A'])

    # Convertir el DataFrame a una lista y obtener las cabeceras
    data = list(df.values)
    headers = df.columns.tolist()

    # Establecer los índices de las columnas relevantes
    lat_idx = headers.index("LAT") - 1 # EL -1 POR Q SI NO LEE LA COLUMNA DE LA DERECHA 
    lon_idx = headers.index("LON") - 1
    ti_idx = headers.index("TI") - 1
    h_idx = headers.index("H") - 1

    # Crear un conjunto para almacenar los pares de vuelos consecutivos
    contiguous_pairs = set()

    # Inicializar variables para el primer TI y sus coordenadas
    prev_ti = None
    prev_coordinates = {'U': 0, 'V': 0}

    # Recorrer todas las filas del CSV (desde la primera fila en adelante)
    for i in range(len(data)):
        row_data = data[i]  # Obtener los datos de la fila actual

        # Obtener el TI, latitud, longitud y altitud de la fila actual
        current_ti = str(row_data[ti_idx])  # Asegurándonos de que TI es siempre una cadena
        lat = row_data[lat_idx]
        lon = row_data[lon_idx]
        alt = row_data[h_idx]

        # Reemplazar comas por puntos y convertir a tipo float
        lat = float(lat.replace(",", "."))
        lon = float(lon.replace(",", "."))
        alt = float(alt.replace(",", "."))

        # Convertir las coordenadas a estereográficas para el vuelo actual
        stereographical_coords_current = get_stereographical_from_lat_lon_alt(lat, lon, alt)

        # Acceder a las coordenadas 'U' y 'V' del diccionario
        U1 = stereographical_coords_current['U']
        V1 = stereographical_coords_current['V']

        # Si tenemos un TI diferente al anterior, comprobamos si hay que agregar el par
        if prev_ti is not None and prev_ti != current_ti:
            # Calcular la distancia entre el vuelo anterior y el actual
            distance = calculate_distance(prev_coordinates['U'], prev_coordinates['V'], U1, V1)

            # Si la distancia es menor a 5 NM, agregar el par
            if distance <= 5:  # 5 NM es la distancia máxima para considerar vuelos consecutivos
                # Almacenar la pareja de manera ordenada para evitar duplicados al revés
                pair = tuple(sorted([str(prev_ti), str(current_ti)]))  # Evita duplicados de par invertido
                contiguous_pairs.add(pair)  # set se encarga de evitar duplicados

        # Si el TI es el mismo que el anterior, solo actualizamos las coordenadas
        if prev_ti == current_ti:
            prev_coordinates = stereographical_coords_current
        else:
            # Si es un TI nuevo, lo asignamos a prev_ti
            prev_ti = current_ti
            prev_coordinates = stereographical_coords_current

    # Devolver la lista de pares consecutivos como lista
    return list(contiguous_pairs)
    """
