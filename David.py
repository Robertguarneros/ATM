# Son los q me ha dicho GPT si hay otros mejores se cambia
import tkinter as tk
from datetime import timedelta
from tkinter import filedialog

import pandas as pd
import numpy as np

# Constants
A = 6378137.0  # Semi-major axis in meters
E2 = 0.00669437999014  # Eccentricity squared for WGS84
B = 6356752.3142  # Semi-minor axis in meters


def calculate_rotation_matrix(lat, lon):
    """
    Calculates the rotation matrix for given latitude and longitude (in radians).
    """
    r11 = -np.sin(lon)
    r12 = np.cos(lon)
    r13 = 0
    r21 = -np.sin(lat) * np.cos(lon)
    r22 = -np.sin(lat) * np.sin(lon)
    r23 = np.cos(lat)
    r31 = np.cos(lat) * np.cos(lon)
    r32 = np.cos(lat) * np.sin(lon)
    r33 = np.sin(lat)
    return np.array([[r11, r12, r13], [r21, r22, r23], [r31, r32, r33]])


def calculate_translation_matrix(lat, lon, alt):
    """
    Calculates the translation matrix for a given latitude, longitude (in radians), and altitude (in meters).
    """
    nu = A / np.sqrt(1 - E2 * np.sin(lat) ** 2)
    tx = (nu + alt) * np.cos(lat) * np.cos(lon)
    ty = (nu + alt) * np.cos(lat) * np.sin(lon)
    tz = (nu * (1 - E2) + alt) * np.sin(lat)
    return np.array([tx, ty, tz])


def geodesic_to_geocentric(lat_in, lon_in, alt_in):
    """
    Converts geodetic coordinates (latitude, longitude, height) to geocentric (x, y, z).
    """

    lat = float(lat_in.replace(",", ".")),
    lon = float(lon_in.replace(",", ".")),
    alt = float(alt_in.replace(",", "."))

    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    nu = A / np.sqrt(1 - E2 * np.sin(lat_rad) ** 2)

    x = (nu + alt) * np.cos(lat_rad) * np.cos(lon_rad)
    y = (nu + alt) * np.cos(lat_rad) * np.sin(lon_rad)
    z = (nu * (1 - E2) + alt) * np.sin(lat_rad)
    return np.array([x, y, z])


def get_rotation_matrix(lat, lon):
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    return np.array(
        [
            [-np.sin(lon_rad), np.cos(lon_rad), 0],
            [
                -np.sin(lat_rad) * np.cos(lon_rad),
                -np.sin(lat_rad) * np.sin(lon_rad),
                np.cos(lat_rad),
            ],
            [
                np.cos(lat_rad) * np.cos(lon_rad),
                np.cos(lat_rad) * np.sin(lon_rad),
                np.sin(lat_rad),
            ],
        ]
    )


def get_translation_vector(lat, lon, alt):
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    nu = A / np.sqrt(1 - E2 * np.sin(lat_rad) ** 2)
    return np.array(
        [
            [(nu + alt) * np.cos(lat_rad) * np.cos(lon_rad)],
            [(nu + alt) * np.cos(lat_rad) * np.sin(lon_rad)],
            [(nu * (1 - E2) + alt) * np.sin(lat_rad)],
        ]
    )


def geocentric_to_system_cartesian(geocentric_coords):
    geo = {
        "X": geocentric_coords[0],
        "Y": geocentric_coords[1],
        "Z": geocentric_coords[2],
    }
    center = {"Lat": 41.10904, "Lon": 1.226947, "Alt": 3438.954}
    R = get_rotation_matrix(center["Lat"], center["Lon"])
    T = get_translation_vector(center["Lat"], center["Lon"], center["Alt"])

    input_vector = np.array([[geo["X"]], [geo["Y"]], [geo["Z"]]])
    result_vector = R @ (input_vector - T)

    return {
        "X": result_vector[0, 0],
        "Y": result_vector[1, 0],
        "Z": result_vector[2, 0],
    }


def system_cartesian_to_system_stereographical(c):
    class CoordinatesUVH:
        def __init__(self):
            self.U = 0
            self.V = 0
            self.Height = 0

    res = CoordinatesUVH()
    center = {"Lat": 41.10904, "Lon": 1.226947, "Alt": 3438.954}

    lat_rad = np.radians(center["Lat"])

    R_S = (A * (1.0 - E2)) / (1 - E2 * np.sin(lat_rad) ** 2) ** 1.5

    d_xy2 = c["X"] ** 2 + c["Y"] ** 2
    res.Height = np.sqrt(d_xy2 + (c["Z"] + center["Alt"] + R_S) ** 2) - R_S

    k = (2 * R_S) / (2 * R_S + center["Alt"] + c["Z"] + res.Height)
    res.U = k * c["X"]
    res.V = k * c["Y"]

    return {"U": res.U, "V": res.V, "Height": res.Height}


def get_stereographical_from_lat_lon_alt(lat, lon, alt):
    geocentric_coords = geodesic_to_geocentric(lat, lon, alt)
    cartesian_coords = geocentric_to_system_cartesian(geocentric_coords)
    stereographical_coords = system_cartesian_to_system_stereographical(
        cartesian_coords
    )
    return stereographical_coords

def calculate_distance(U1, V1, U2, V2):
    distance = (
        np.sqrt((U1 - U2) ** 2 + (V1 - V2) ** 2) / 1852
    )  # Return distance in nautical miles
    return distance

def extract_contiguous_pairs():

    # Cargar el archivo
    df = pd.read_excel("assets/InputFiles/2305_02_dep_lebl.xlsx")

    time_threshold_minutes = 4

    # Convertir la columna 'HoraDespegue' a tipo datetime
    df["HoraDespegue"] = pd.to_datetime(df["HoraDespegue"])

    # Ordenar por 'HoraDespegue'
    df_sorted = df.sort_values(by="HoraDespegue").reset_index(drop=True)

    # Listas para almacenar los vuelos contiguos por pista
    contiguous_flights_24L = []
    contiguous_flights_06R = []

    # Lista para almacenar la información adicional
    flight_info_list = []

    # Iterar sobre las filas para calcular diferencias entre vuelos consecutivos
    for i in range(len(df_sorted) - 1):
        current_flight = df_sorted.iloc[i]
        next_flight = df_sorted.iloc[i + 1]

        # Calcular la diferencia de tiempo entre vuelos consecutivos
        time_difference = next_flight["HoraDespegue"] - current_flight["HoraDespegue"]

        if time_difference < timedelta(minutes=time_threshold_minutes):
            # Verificar la pista de despegue y añadir al grupo correspondiente
            if (
                current_flight["PistaDesp"] == "LEBL-24L"
                and next_flight["PistaDesp"] == "LEBL-24L"
            ):
                contiguous_flights_24L.append(
                    (current_flight["Indicativo"], next_flight["Indicativo"])
                )
            elif (
                current_flight["PistaDesp"] == "LEBL-06R"
                and next_flight["PistaDesp"] == "LEBL-06R"
            ):
                contiguous_flights_06R.append(
                    (current_flight["Indicativo"], next_flight["Indicativo"])
                )

        # Añadir información adicional del vuelo a la lista
        flight_info_list.append({
            "Indicativo": current_flight["Indicativo"],
            "Estela": current_flight["Estela"],
            "TipoAeronave": current_flight["TipoAeronave"],
            "ProcDesp": current_flight["ProcDesp"],
        })

    # Incluir la información del último vuelo en la lista
    last_flight = df_sorted.iloc[-1]
    flight_info_list.append({
        "Indicativo": last_flight["Indicativo"],
        "Estela": last_flight["Estela"],
        "TipoAeronave": last_flight["TipoAeronave"],
        "ProcDesp": last_flight["ProcDesp"],
    })

    # Convertir la lista de información en un DataFrame
    flight_info = pd.DataFrame(flight_info_list)

    return contiguous_flights_24L, contiguous_flights_06R, flight_info

def load_data_from_csv(file_path):
    """Carga datos del CSV y devuelve la lista de datos y cabeceras."""
    df = pd.read_csv(file_path, sep=';', na_values=['N/A'])
    data = list(df.values)
    headers = df.columns.tolist()
    return data, headers
    
def compare_radar_separation(contiguous_flights_dist):

    radar_min_separation = 3  # Separación mínima Radar en NM
    results = []
    compliant_pairs = 0  # Contador de parejas que cumplen con el requisito

    # Iterar sobre las parejas y sus distancias mínimas
    for pair, contiguous_flights_dist in contiguous_flights_dist.items():
        # Verificar si cumple con la separación mínima del radar
        is_compliant = contiguous_flights_dist > radar_min_separation
        results.append((pair[0], pair[1], contiguous_flights_dist, is_compliant))

        # Contar cuántas cumplen la condición
        if is_compliant:
            compliant_pairs += 1
    
    # Calcular el porcentaje de cumplimiento
    total_pairs = len(contiguous_flights_dist)
    compliance_percentage = (compliant_pairs / total_pairs * 100) if total_pairs > 0 else 0

    return results, compliance_percentage

def compare_wake_separation(contiguous_flights_dist, flight_info):

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

    # Crear un diccionario con la estela de cada indicativo
    estela_by_indicativo = flight_info.set_index("Indicativo")["Estela"].to_dict()
    
    results = []
    compliant_pairs = 0  # Contador de parejas que cumplen la condición

    for pair, min_distance in contiguous_flights_dist.items():
        ti_1, ti_2 = pair

        # Obtener los tipos de aeronave para ambos vuelos
        wake_class_1 = estela_by_indicativo.get(ti_1, 'Desconocido')
        wake_class_2 = estela_by_indicativo.get(ti_2, 'Desconocido')

        # Buscar la separación mínima de estela basada en el tipo de aeronave
        wake_min_separation = wake_separation_table.get((wake_class_1, wake_class_2), None)

        # Verificar si la distancia mínima cumple con la separación por estela
        is_compliant = False
        if wake_min_separation is not None and min_distance > wake_min_separation:
            is_compliant = True
        
        # Agregar el resultado con la distancia mínima, tipos de aeronave y si cumple o no
        results.append((ti_1, ti_2, min_distance, f"{wake_class_1}", f"{wake_class_2}", wake_min_separation, is_compliant))

        # Contar cuántas parejas cumplen con la condición
        if is_compliant:
            compliant_pairs += 1
    
    # Calcular el porcentaje de cumplimiento
    total_pairs = len(contiguous_flights_dist)
    compliance_percentage = (compliant_pairs / total_pairs * 100) if total_pairs > 0 else 0

    return results, compliance_percentage

def compare_loa_separation(contiguous_flights_dist, flight_info):
    """
    Compara la separación LoA entre pares de vuelos y calcula el porcentaje de cumplimiento
    según la distancia mínima calculada y las categorías de aeronave.
    
    Args:
        contiguous_flights_dist (dict): Diccionario con las distancias mínimas calculadas por pareja.
        flight_info (pd.DataFrame): DataFrame con la información de los vuelos, que contiene 'Indicativo', 'TipoAeronave', 'ProcDesp'.
        
    Returns:
        tuple: Una lista con las parejas que cumplen o no con la separación mínima LoA y el porcentaje de cumplimiento.
    """
    # Definir la tabla de separación LoA
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

    # Diccionarios con tipo de aeronave y procedimientos de despegue por indicativo
    tipoAeronave_by_indicativo = flight_info.set_index("Indicativo")["TipoAeronave"].to_dict()
    proc_desp_by_indicativo = flight_info.set_index("Indicativo")["ProcDesp"].to_dict()

    # Definir las categorías directamente
    aircraft_classification = pd.read_excel("assets/InputFiles/Tabla_Clasificacion_aeronaves.xlsx")
    categories = {
        "HP": set(aircraft_classification["HP"].dropna().tolist()),
        "NR": set(aircraft_classification["NR"].dropna().tolist()),
        "NR+": set(aircraft_classification["NR+"].dropna().tolist()),
        "NR-": set(aircraft_classification["NR-"].dropna().tolist()),
        "LP": set(aircraft_classification["LP"].dropna().tolist()),
    }

    # Lista para guardar los resultados
    results = []
    compliant_pairs = 0  # Contador de parejas que cumplen la separación

    # Procesar cada par de vuelos en contiguous_pairs
    for pair, min_distance in contiguous_flights_dist.items():
        ti_1, ti_2 = pair

        tipo_1 = tipoAeronave_by_indicativo.get(ti_1, "Desconocido")
        tipo_2 = tipoAeronave_by_indicativo.get(ti_2, "Desconocido")
        sid_1 = proc_desp_by_indicativo.get(ti_1, "Desconocido")
        sid_2 = proc_desp_by_indicativo.get(ti_2, "Desconocido")

        if "Desconocido" in (tipo_1, tipo_2, sid_1, sid_2):
            continue  # Si hay algún dato desconocido, omitimos esta pareja

        # Clasificar las aeronaves directamente
        category_1 = next((cat for cat, types in categories.items() if tipo_1 in types), "R")
        category_2 = next((cat for cat, types in categories.items() if tipo_2 in types), "R")
        same_sid = "Misma" if sid_1 == sid_2 else "Distinta"

        # Obtener la separación mínima de la tabla LoA
        separation_key = (category_1, category_2, same_sid)
        min_separation = loa_separation.get(separation_key, 3)

        # Verificar si la distancia mínima cumple con la separación
        is_compliant = min_distance < min_separation
        if is_compliant:
            compliant_pairs += 1

        # Agregar los resultados
        results.append((ti_1, ti_2, min_distance, category_1, category_2, min_separation, same_sid, is_compliant))

    # Calcular el porcentaje de cumplimiento
    total_pairs = len(contiguous_flights_dist)
    compliance_percentage = (compliant_pairs / total_pairs) * 100 if total_pairs > 0 else 0

    return results, compliance_percentage

# Función para seleccionar el archivo CSV
def select_file():
    root = tk.Tk()  # Crear una ventana raíz
    root.withdraw()  # Ocultar la ventana raíz
    file_path = filedialog.askopenfilename(title="Selecciona un archivo CSV", filetypes=[("CSV files", "*.csv")])  # Abrir el cuadro de diálogo
    return file_path

def calculate_min_distances(csv_file_path, contiguous_flights_06R): # añadir en caso de hacer os dos a la vez contiguous_flights_24L
    # Leer el archivo CSV
    df = pd.read_csv(csv_file_path, sep=';', na_values=['N/A'])
    
    # Convertir el DataFrame a una lista y obtener las cabeceras
    data = list(df.values)
    headers = df.columns.tolist()

    # Establecer los índices de las columnas relevantes
    lat_idx = headers.index("LAT")-1 # EL -1 ESTA POR Q SI NO LEE LA COLUMNA DE LA DERECHA
    lon_idx = headers.index("LON")-1
    ti_idx = headers.index("TI")-1
    h_idx = headers.index("H")-1

    #results_24L = {}
    results_06R = {}

    '''
    EN CASO DE QUERER HACER LOS CALCULOS PARA LS DOS PISTAS A LA VEZ

    # Calcular las distancias mínimas para las parejas de la pista 24L
    for pair in contiguous_flights_24L:
        plane1, plane2 = pair
        min_distance = float('inf')
        found = False
        
        for row_1 in data:
            if row_1[ti_idx] != plane1:
                continue
            for row_2 in data:
                if row_2[ti_idx] != plane2:
                    continue
                
                # Verificar condición para la pista 24L
                if row_1[lon_idx] < '2,073776' and row_2[lon_idx] < '2.073776' and row_1[lat_idx] < '41,292008' and row_2[lat_idx] < '41,292008':
                    coords_1 = get_stereographical_from_lat_lon_alt(row_1[lat_idx], row_1[lon_idx], row_1[h_idx])
                    coords_2 = get_stereographical_from_lat_lon_alt(row_2[lat_idx], row_2[lon_idx], row_2[h_idx])
                    dist = calculate_distance(coords_1['U'], coords_1['V'], coords_2['U'], coords_2['V']).item()
                    min_distance = min(min_distance, dist)
                    found = True
        
        if found and min_distance != float('inf'):
            results_24L[pair] = min_distance
    '''
    # Calcular las distancias mínimas para las parejas de la pista 06R
    for pair in contiguous_flights_06R:
        plane1, plane2 = pair
        min_distance = float('inf')
        found = False
        
        for row_1 in data:
            if row_1[ti_idx] != plane1:
                continue
            for row_2 in data:
                if row_2[ti_idx] != plane2:
                    continue
                
                # Verificar condición para la pista 06R
                if row_1[lon_idx] > '2,103790' and row_2[lon_idx] > '2,103790' and row_1[lat_idx] < '41,292008' and row_2[lat_idx] < '41,292008':
                    coords_1 = get_stereographical_from_lat_lon_alt(row_1[lat_idx], row_1[lon_idx], row_1[h_idx])
                    coords_2 = get_stereographical_from_lat_lon_alt(row_2[lat_idx], row_2[lon_idx], row_2[h_idx])
                    dist = calculate_distance(coords_1['U'], coords_1['V'], coords_2['U'], coords_2['V']).item()
                    min_distance = min(min_distance, dist)
                    found = True
        
        if found and min_distance != float('inf'):
            results_06R[pair] = min_distance

    return results_06R #, results_06R



# Extraer los datos contiguos y la tabla de información de vuelos
contiguous_flights_24L, contiguous_flights_06R, flight_info = extract_contiguous_pairs()
csv_file_path = select_file()
results_06R = calculate_min_distances(csv_file_path, contiguous_flights_06R)
results, compliance_percentage = compare_loa_separation(results_06R, flight_info)
print(results)
print(compliance_percentage)