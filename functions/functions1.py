# Son los q me ha dicho GPT si hay otros mejores se cambia
import csv
import math
import re
from datetime import timedelta

import numpy as np
import pandas as pd

# Constants
A = 6378137.0  # Semi-major axis in meters
E2 = 0.00669437999014  # Eccentricity squared for WGS84
B = 6356752.3142  # Semi-minor axis in meters


# Load flight data
def load_24h(file1, file2, file3, file4, file5, file6):
    # Initialize an empty matrix to hold all data
    matrix = []
    first_file = True  # Flag to indicate if it's the first file being processed

    for file in [file1, file2, file3, file4, file5, file6]:
        with open(file, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=";")

            # Skip the header for all files except the first
            if not first_file:
                next(reader, None)  # Skip the header row
            else:
                first_file = False  # Ensure subsequent files skip the header

            # Generate a matrix by reading all rows
            for row in reader:
                # Replace commas with dots, excluding column 23, and replace 'NV' with 'N/A'
                processed_row = [
                    (
                        cell.replace(",", ".").replace("NV", "N/A")
                        if "," in cell and i != 23
                        else cell.replace("NV", "N/A")
                    )
                    for i, cell in enumerate(row)
                ]
                matrix.append(processed_row)

            # Remove the 25th column (index 24) from each row
            for row in matrix:
                if len(row) > 24:  # Ensure row has at least 25 columns
                    del row[24]  # Remove the 25th column

    return matrix


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


def geodesic_to_geocentric(lat, lon, alt):
    """
    Converts geodetic coordinates (latitude, longitude, height) to geocentric (x, y, z).
    """

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


def corrected_altitude(BarometricPressureSetting, FlightLevel):
    altitude_in_feet_corrected = 0
    if BarometricPressureSetting != "N/A":
        QNH_actual = float(BarometricPressureSetting)
        QNH_standard = 1013.2
        if float(FlightLevel) < 60:
            if 1013 <= QNH_actual <= 1013.3:
                altitude_in_feet_corrected = float(FlightLevel) * 100
            else:
                altitude_in_feet_corrected = (
                    float(float(FlightLevel) * 100) + (QNH_actual - QNH_standard) * 30
                )
                altitude_in_feet_corrected = round(altitude_in_feet_corrected, 2)
        else:
            altitude_in_feet_corrected = float(FlightLevel) * 100
    return altitude_in_feet_corrected


def calculate_distance(U1, V1, U2, V2):
    distance = (
        np.sqrt((U1 - U2) ** 2 + (V1 - V2) ** 2) / 1852
    )  # Return distance in nautical miles
    return distance


# Insert corrected altitude for a file at the last column
def correct_altitude_for_file(matrix):
    # Add a column that has the corrected altitude
    # Find the column indices for BP (Barometric Pressure) and FL (Flight Level)
    bp_index = matrix[0].index("BP")
    fl_index = matrix[0].index("FL")

    # Check if "CorrectedAltitude" already exists in the header
    if "CorrectedAltitude" not in matrix[0]:
        matrix[0].append(
            "CorrectedAltitude"
        )  # Append the header for the corrected altitude

    # Process each row (skip the header)
    for row in matrix[1:]:
        # Avoid appending if the corrected altitude is already present
        if len(row) == len(matrix[0]):
            continue  # Skip rows that already have the corrected altitude
        barometric_pressure = row[bp_index]
        flight_level = row[fl_index]
        corrected_alt = corrected_altitude(barometric_pressure, flight_level)
        row.append(corrected_alt)

    return matrix


# Load DEP file
def load_departures():
    """
    Load departures data from a file-like object (e.g., UploadedFile from Streamlit).
    """
    # Read the Excel file directly from the file-like object
    df = pd.read_excel("assets/InputFiles/2305_02_dep_lebl.xlsx")

    # Include the header row in the matrix
    matrix = [df.columns.tolist()] + df.values.tolist()

    return matrix


# Load flight data
def load_flights(file_path):
    # Open the CSV file
    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=";")

        # Generate a matrix by reading all rows
        matrix = []
        for row in reader:
            # Replace commas with dots, excluding column 23, and replace 'NV' with 'N/A'
            processed_row = [
                (
                    cell.replace(",", ".").replace("NV", "N/A")
                    if "," in cell and i != 23
                    else cell.replace("NV", "N/A")
                )
                for i, cell in enumerate(row)
            ]
            matrix.append(processed_row)

        # Remove the 25th column (index 24) from each row
        for row in matrix:
            if len(row) > 24:  # Ensure row has at least 25 columns
                del row[24]  # Remove the 25th column

    return matrix


# Get trajectory for an airplane
def get_trajectory_for_airplane(loaded_departures, loaded_flights):
    # Find the relevant column indices
    indicativo_index = loaded_departures[0].index("Indicativo")
    ti_index = loaded_flights[0].index("TI")
    time_index = loaded_flights[0].index("TIME(s)")
    lat_index = loaded_flights[0].index("LAT")
    lon_index = loaded_flights[0].index("LON")
    h_index = loaded_flights[0].index("H")
    corrected_altitude_index = loaded_flights[0].index("CorrectedAltitude")
    ias_index = loaded_flights[0].index("IAS")

    # Extract all unique flight identifiers from departures
    flight_identifiers = set(row[indicativo_index] for row in loaded_departures[1:])

    # Prepare the trajectory dictionary
    trajectories = {flight: [] for flight in flight_identifiers}

    # Iterate through flights to calculate the route
    for row in loaded_flights[1:]:
        # Get the current flight identifier (TI column)
        flight_identifier = row[ti_index]

        # Check if this flight identifier is in the departures
        if flight_identifier in trajectories:
            # Extract relevant data for this row
            time = row[time_index]
            lat = row[lat_index]
            lon = row[lon_index]
            h = row[h_index]
            corrected_altitude = row[corrected_altitude_index]
            ias = row[ias_index]

            if ias != "N/A":
                # Save the data for the trajectory
                trajectories[flight_identifier].append(
                    {
                        "time": time,
                        "latitude": lat,
                        "longitude": lon,
                        "height": h,
                        "corrected_altitude": corrected_altitude,
                        "ias": ias,
                    }
                )

    return trajectories


def filter_empty_trajectories(trajectories):
    # Create a new dictionary containing only flights with non-empty trajectories
    filtered_trajectories = {
        flight_id: points
        for flight_id, points in trajectories.items()
        if points  # Keep only if the points list is not empty
    }
    return filtered_trajectories


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

    # Función para extraer la base de la SID (antes del número)
    def extract_base_sid(sid):
        # Usamos expresión regular para quitar los números al final de la SID
        base_sid = re.match(
            r"([A-Za-z]+)", sid
        )  # Solo toma letras antes de cualquier número
        return (
            base_sid.group(0) if base_sid else sid
        )  # Si no encuentra nada, devuelve la SID completa

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

        # Procesar la SID (ProcDesp) para eliminar el número y dejar solo el nombre base
        base_sid = extract_base_sid(current_flight["ProcDesp"])

        # Añadir información adicional del vuelo a la lista
        flight_info_list.append(
            {
                "Indicativo": current_flight["Indicativo"],
                "Estela": current_flight["Estela"],
                "TipoAeronave": current_flight["TipoAeronave"],
                "ProcDesp": base_sid,  # Guardar solo el nombre base de la SID
            }
        )

    # Incluir la información del último vuelo en la lista
    last_flight = df_sorted.iloc[-1]
    base_sid_last = extract_base_sid(
        last_flight["ProcDesp"]
    )  # Procesar la SID del último vuelo
    flight_info_list.append(
        {
            "Indicativo": last_flight["Indicativo"],
            "Estela": last_flight["Estela"],
            "TipoAeronave": last_flight["TipoAeronave"],
            "ProcDesp": base_sid_last,  # Guardar solo el nombre base de la SID
        }
    )

    # Convertir la lista de información en un DataFrame
    flight_info = pd.DataFrame(flight_info_list)

    return contiguous_flights_24L, contiguous_flights_06R, flight_info


def load_data_from_csv(file_path):
    """Carga datos del CSV y devuelve la lista de datos y cabeceras."""
    df = pd.read_csv(file_path, sep=";", na_values=["N/A"])
    data = list(df.values)
    headers = df.columns.tolist()
    return data, headers


def compare_radar_separation(contiguous_flights_dist):
    radar_min_separation = 3  # Separación mínima Radar en NM
    results = []
    compliant_pairs = 0  # Contador de parejas que cumplen con el requisito

    # Iterar sobre las parejas y sus distancias mínimas
    for pair, distance in contiguous_flights_dist.items():
        # Verificar si cumple con la separación mínima del radar
        is_compliant = distance > radar_min_separation
        results.append((pair[0], pair[1], distance, is_compliant))

        # Contar cuántas cumplen la condición
        if is_compliant:
            compliant_pairs += 1

    # Calcular el porcentaje de cumplimiento
    total_pairs = len(contiguous_flights_dist)
    compliance_percentage = (
        (compliant_pairs / total_pairs * 100) if total_pairs > 0 else 0
    )

    return results, compliance_percentage


def compare_wake_separation(contiguous_flights_dist, flight_info):

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

    # Crear un diccionario con la estela de cada indicativo
    estela_by_indicativo = flight_info.set_index("Indicativo")["Estela"].to_dict()

    results = []
    compliant_pairs = 0  # Contador de parejas que cumplen la condición

    for pair, min_distance in contiguous_flights_dist.items():
        ti_1, ti_2 = pair

        # Obtener los tipos de aeronave para ambos vuelos
        wake_class_1 = estela_by_indicativo.get(ti_1, "Desconocido")
        wake_class_2 = estela_by_indicativo.get(ti_2, "Desconocido")

        # Buscar la separación mínima de estela basada en el tipo de aeronave
        wake_min_separation = wake_separation_table.get(
            (wake_class_1, wake_class_2), None
        )

        # Verificar si la distancia mínima cumple con la separación por estela
        is_compliant = False
        if wake_min_separation is not None and min_distance > wake_min_separation:
            is_compliant = True

        # Agregar el resultado con la distancia mínima, tipos de aeronave y si cumple o no
        results.append(
            (
                ti_1,
                ti_2,
                min_distance,
                f"{wake_class_1}",
                f"{wake_class_2}",
                wake_min_separation,
                is_compliant,
            )
        )

        # Contar cuántas parejas cumplen con la condición
        if is_compliant:
            compliant_pairs += 1

    # Calcular el porcentaje de cumplimiento
    total_pairs = len(contiguous_flights_dist)
    compliance_percentage = (
        (compliant_pairs / total_pairs * 100) if total_pairs > 0 else 0
    )

    return results, compliance_percentage


def compare_loa_separation(contiguous_flights_dist, flight_info):

    # Cargar los archivos de SIDs agrupadas directamente como diccionarios
    sid_24L_df = pd.read_excel("assets/InputFiles/Tabla_misma_SID_24L.xlsx")
    sid_06R_df = pd.read_excel("assets/InputFiles/Tabla_misma_SID_06R.xlsx")

    sid_groups_24L = {
        sid.split("-")[0]: col  # Extraer la base de la SID y asignar el grupo
        for col in sid_24L_df.columns
        for sid in sid_24L_df[col].dropna()
    }

    sid_groups_06R = {
        sid.split("-")[0]: col
        for col in sid_06R_df.columns
        for sid in sid_06R_df[col].dropna()
    }

    # Función para determinar el grupo de una SID
    def get_sid_group(sid):
        base = sid.split("-")[0]
        return sid_groups_24L.get(base) or sid_groups_06R.get(base) or "Sin Grupo"

    # Función para determinar si dos SIDs están en el mismo grupo
    def are_sids_in_same_group(sid1, sid2):
        group1 = get_sid_group(sid1)
        group2 = get_sid_group(sid2)
        return group1 == group2 if group1 and group2 else False

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
    tipoAeronave_by_indicativo = flight_info.set_index("Indicativo")[
        "TipoAeronave"
    ].to_dict()
    proc_desp_by_indicativo = flight_info.set_index("Indicativo")["ProcDesp"].to_dict()

    # Definir las categorías directamente
    aircraft_classification = pd.read_excel(
        "assets/InputFiles/Tabla_Clasificacion_aeronaves.xlsx"
    )
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
        category_1 = next(
            (cat for cat, types in categories.items() if tipo_1 in types), "R"
        )
        category_2 = next(
            (cat for cat, types in categories.items() if tipo_2 in types), "R"
        )

        # Determinar si están en el mismo grupo de SID
        same_sid = "Misma" if are_sids_in_same_group(sid_1, sid_2) else "Distinta"

        # Obtener el grupo de la SID del segundo avión
        group_2 = get_sid_group(sid_2)

        # Obtener la separación mínima de la tabla LoA
        separation_key = (category_1, category_2, same_sid)
        min_separation = loa_separation.get(separation_key, 3)

        # Verificar si la distancia mínima cumple con la separación
        is_compliant = min_distance > min_separation
        if is_compliant:
            compliant_pairs += 1

        # Agregar los resultados
        results.append(
            (
                ti_1,
                ti_2,
                min_distance,
                category_1,
                category_2,
                min_separation,
                same_sid,
                group_2,
                is_compliant,
            )
        )

    # Calcular el porcentaje de cumplimiento
    total_pairs = len(contiguous_flights_dist)
    compliance_percentage = (
        (compliant_pairs / total_pairs) * 100 if total_pairs > 0 else 0
    )

    return results, compliance_percentage


# Constantes globales
RADIUS_EARTH_KM = 6371.0  # Radio de la Tierra en kilómetros

# Función para calcular la distancia haversine
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return RADIUS_EARTH_KM * c

# Función para verificar si un punto está dentro del área circular
def is_within_circle(lat, lon, center, radius_km):
    distance = haversine(lat, lon, center[0], center[1])
    return distance <= radius_km


def calculate_min_distances(
    loaded_departures, loaded_flights, contiguous_flights_24L, contiguous_flights_06R
):
    trajectories = get_trajectory_for_airplane(loaded_departures, loaded_flights)
    trajectories = filter_empty_trajectories(trajectories)  # Filtrar trayectorias vacías

    # Configurar las áreas circulares
    threshold_06R_center = (41.291979, 2.104396)
    threshold_24L_center = (41.281960, 2.073305)
    RADIUS_NM = 100  # Radio en millas náuticas
    RADIUS_KM = RADIUS_NM * 1.852  # Convertir a kilómetros

    results_24L_TMA = {}
    results_06R_TMA = {}

    def calculate_distances_for_pairs(pairs, threshold_center, radius_km, results):
        for pair in pairs:
            plane1, plane2 = pair
            min_distance = float("inf")  # Inicializar la distancia mínima
            inside_area = False  # Para rastrear si el avión 2 está dentro del área

            # Obtener las trayectorias para ambos vuelos
            traj1 = trajectories.get(plane1, [])
            traj2 = trajectories.get(plane2, [])

            # Indexar las trayectorias por tiempo para emparejarlas
            traj1_by_time = {float(point["time"]): point for point in traj1}
            traj2_by_time = {float(point["time"]): point for point in traj2}

            # Buscar tiempos comunes
            common_times = sorted(set(traj1_by_time.keys()) & set(traj2_by_time.keys()))

            for time in common_times:
                point_1 = traj1_by_time[time]
                point_2 = traj2_by_time[time]

                lat_1, lon_1, h_1 = (
                    float(point_1["latitude"]),
                    float(point_1["longitude"]),
                    float(point_1["height"]),
                )
                lat_2, lon_2, h_2 = (
                    float(point_2["latitude"]),
                    float(point_2["longitude"]),
                    float(point_2["height"]),
                )

                if not inside_area and is_within_circle(lat_2, lon_2, threshold_center, radius_km):
                    inside_area = True  # Empieza a calcular cuando el avión 2 entra en el área

                if inside_area:
                    coords_1 = get_stereographical_from_lat_lon_alt(lat_1, lon_1, h_1)
                    coords_2 = get_stereographical_from_lat_lon_alt(lat_2, lon_2, h_2)

                    # Calcular distancia en 3D
                    dist = calculate_distance(
                        coords_1["U"], coords_1["V"], coords_2["U"], coords_2["V"]
                    ).item()

                    min_distance = min(min_distance, dist)  # Actualizar la distancia mínima

            if min_distance != float("inf"):
                results[pair] = min_distance

    # Procesar cada conjunto de vuelos para las pistas
    calculate_distances_for_pairs(
        contiguous_flights_24L, threshold_24L_center, RADIUS_KM, results_24L_TMA
    )
    calculate_distances_for_pairs(
        contiguous_flights_06R, threshold_06R_center, RADIUS_KM, results_06R_TMA
    )

    return results_24L_TMA, results_06R_TMA




def calculate_exit_distances(
    loaded_departures, loaded_flights, contiguous_flights_24L, contiguous_flights_06R
):
    trajectories = get_trajectory_for_airplane(loaded_departures, loaded_flights)
    trajectories = filter_empty_trajectories(trajectories)  # Filtrar trayectorias vacías

    RADIUS_NM = 0.5  # Radio en millas náuticas
    RADIUS_KM = RADIUS_NM * 1.852  # Convertimos el radio a kilómetros

    threshold_06R_center = (41.282311, 2.074351)
    threshold_24L_center = (41.291997, 2.103112)

    results_24L_TWR = {}
    results_06R_TWR = {}

    def calculate_distances_for_pairs(pairs, center, radius_km, results):
        for pair in pairs:
            plane1, plane2 = pair
            min_distance = float("inf")
            found = False

            traj1 = trajectories.get(plane1, [])
            traj2 = trajectories.get(plane2, [])

            traj1_by_time = {float(point["time"]): point for point in traj1}
            traj2_by_time = {float(point["time"]): point for point in traj2}

            common_times = sorted(set(traj1_by_time.keys()) & set(traj2_by_time.keys()))

            inside_area = False  # Para rastrear si el avión 2 estaba dentro del área

            for time in common_times:
                point_1 = traj1_by_time[time]
                point_2 = traj2_by_time[time]

                lat_1, lon_1, h_1 = (
                    float(point_1["latitude"]),
                    float(point_1["longitude"]),
                    float(point_1["height"]),
                )
                lat_2, lon_2, h_2 = (
                    float(point_2["latitude"]),
                    float(point_2["longitude"]),
                    float(point_2["height"]),
                )

                # Verificar si el avión 2 está dentro del área
                if is_within_circle(lat_2, lon_2, center, radius_km):
                    inside_area = True
                    continue  # Ignorar mientras el avión 2 esté dentro del área

                # Si el avión 2 acaba de salir del área, calcular distancia
                if inside_area:
                    coords_1 = get_stereographical_from_lat_lon_alt(lat_1, lon_1, h_1)
                    coords_2 = get_stereographical_from_lat_lon_alt(lat_2, lon_2, h_2)

                    dist = calculate_distance(
                        coords_1["U"], coords_1["V"], coords_2["U"], coords_2["V"]
                    ).item()

                    min_distance = min(min_distance, dist)
                    found = True
                    break  # Solo calcular para la primera salida del área

            if found and min_distance != float("inf"):
                results[pair] = min_distance

    calculate_distances_for_pairs(
        contiguous_flights_24L, threshold_24L_center, RADIUS_KM, results_24L_TWR
    )
    calculate_distances_for_pairs(
        contiguous_flights_06R, threshold_06R_center, RADIUS_KM, results_06R_TWR
    )

    return results_24L_TWR, results_06R_TWR




def general(file_path):

    # Funciones
    csv_file = file_path
    contiguous_flights_24L, contiguous_flights_06R, flight_info = (
        extract_contiguous_pairs()
    )
    dep = load_departures()
    csv_file_alt = correct_altitude_for_file(csv_file)
    results_24L_TMA, results_06R_TMA = calculate_min_distances(
        dep, csv_file_alt, contiguous_flights_24L, contiguous_flights_06R
    )
    results_24L_TWR, results_06R_TWR = calculate_exit_distances(
        dep, csv_file_alt, contiguous_flights_24L, contiguous_flights_06R
    )

    return results_24L_TMA, results_06R_TMA, results_24L_TWR, results_06R_TWR, flight_info


'''
file_path = "assets/CsvFiles/P3_08_12h.csv"
results_24L_TMA, results_06R_TMA, results_24L_TWR, results_06R_TWR, flight_info = general(file_path)
print(results_24L_TMA,"\n")
print(results_24L_TWR,"\n")

# Poner la funcion q sea para ver la salida
results, compliance_percentage = compare_loa_separation(results_24L_TWR, flight_info) # flight_info    en caso de utilizar el wake oel loa
'''
