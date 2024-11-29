import pandas as pd
import numpy as np

# Son los q me ha dicho GPT si hay otros mejores se cambia
import tkinter as tk
from tkinter import filedialog 

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
    if BarometricPressureSetting!= "N/A":
        QNH_actual = float(BarometricPressureSetting)
        QNH_standard = 1013.2
        if float(FlightLevel) < 60:
            if 1013 <= QNH_actual <= 1013.3:
                altitude_in_feet_corrected = FlightLevel * 100
            else:
                altitude_in_feet_corrected = (
                    float((FlightLevel) * 100)
                    + (QNH_actual - QNH_standard) * 30
                )
                altitude_in_feet_corrected = round(
                    altitude_in_feet_corrected, 2
                )
    return altitude_in_feet_corrected

def calculate_distance(U1, V1, U2, V2):
    distance = np.sqrt((U1 - U2) ** 2 + (V1 - V2) ** 2) / 1852 # Return distance in nautical miles
    return distance


def extract_contiguous_pairs(file_path):
    # Leer el archivo con el delimitador adecuado y manejar valores nulos
    df = pd.read_csv(file_path, sep=';', na_values=['N/A'])

    # Convertir el DataFrame a una lista y obtener las cabeceras
    data = list(df.values)
    headers = df.columns.tolist()

    # Establecer los índices de las columnas relevantes
    lat_idx = headers.index("LAT") - 1
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








# Función para seleccionar el archivo CSV
def select_file():
    root = tk.Tk()  # Crear una ventana raíz
    root.withdraw()  # Ocultar la ventana raíz
    file_path = filedialog.askopenfilename(title="Selecciona un archivo CSV", filetypes=[("CSV files", "*.csv")])  # Abrir el cuadro de diálogo
    return file_path


# Llamada a la función para seleccionar el archivo
file_path = select_file()

# Usar la función con el archivo seleccionado
if file_path:
    pairs = extract_contiguous_pairs(file_path)
    # Mostrar los pares únicos
    print(pairs)
else:
    print("No se seleccionó ningún archivo.")
