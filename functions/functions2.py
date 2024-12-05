import csv

import numpy as np
import pandas as pd

# Load DEP file
def load_departures(file_path):
    df = pd.read_excel(file_path)

    # Include the header row in the matrix
    matrix = [df.columns.tolist()] + df.values.tolist()

    # Return the matrix created
    return matrix



# Load flight data
def load_flights(file_path):
    # Open the CSV file
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        
        # Generate a matrix by reading all rows
        matrix = []
        for row in reader:
            # Replace commas with dots, excluding column 23, and replace 'NV' with 'N/A'
            processed_row = [
                cell.replace(',', '.').replace('NV', 'N/A') if ',' in cell and i != 23 else cell.replace('NV', 'N/A')
                for i, cell in enumerate(row)
            ]
            matrix.append(processed_row)
        
        # Remove the 25th column (index 24) from each row
        for row in matrix:
            if len(row) > 24:  # Ensure row has at least 25 columns
                del row[24]  # Remove the 25th column

    return matrix


def load_files(departures_file, flights_file):
    loaded_departures = load_departures(departures_file)
    loaded_flights = load_flights(flights_file)
    return loaded_departures, loaded_flights


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

def correct_altitude_for_file(matrix):
    # Add a column that has the corrected altitude
    # Find the column indices for BP (Barometric Pressure) and FL (Flight Level)
    bp_index = matrix[0].index("BP")
    fl_index = matrix[0].index("FL")

    # Append a new header for the corrected altitude
    matrix[0].append("CorrectedAltitude")

    # Process each row (skip the header)
    for row in matrix[1:]:
        barometric_pressure = row[bp_index]
        flight_level = row[fl_index]
        corrected_alt = corrected_altitude(barometric_pressure, flight_level)
        row.append(corrected_alt)

    return matrix

def get_trajectory_for_airplane(loaded_departures, loaded_flights):
    # Find the relevant column indices
    indicativo_index = loaded_departures[0].index("Indicativo")
    ti_index = loaded_flights[0].index("TI")
    time_index = loaded_flights[0].index("TIME(s)")
    lat_index = loaded_flights[0].index("LAT")
    lon_index = loaded_flights[0].index("LON")
    h_index = loaded_flights[0].index("H")
    corrected_altitude_index = loaded_flights[0].index("CorrectedAltitude")

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

            # Save the data for the trajectory
            trajectories[flight_identifier].append(
                {
                    "time": time,
                    "latitude": lat,
                    "longitude": lon,
                    "height": h,
                    "corrected_altitude": corrected_altitude,
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

def filter_departures_by_runway(departures_matrix, flights_matrix):
    # Get the header row for each matrix
    departures_header = departures_matrix[0]
    flights_header = flights_matrix[0]

    # Find the index of relevant columns in the departures matrix
    pista_desp_index = departures_header.index('PistaDesp')
    indicativo_index = departures_header.index('Indicativo')

    # Find the index of relevant columns in the flights matrix
    ta_index = flights_header.index('TI')

    # Create a set of all flight identifiers (TI) for quick lookup
    flight_ti_set = {row[ta_index] for row in flights_matrix[1:]}

    # Initialize lists to store matching departures
    matching_departures_6R = []
    matching_departures_24L = []

    # Process the departures matrix once
    for row in departures_matrix[1:]:
        indicativo = row[indicativo_index]
        pista_desp = row[pista_desp_index]

        # Check if the flight matches a TI in the flights matrix
        if indicativo in flight_ti_set:
            if pista_desp == 'LEBL-06R':
                matching_departures_6R.append(indicativo)
            elif pista_desp == 'LEBL-24L':
                matching_departures_24L.append(indicativo)

    return matching_departures_6R, matching_departures_24L

def group_by_aircraft_id(data, id_index):
    grouped_data = {}
    for row in data:
        aircraft_id = row[id_index]
        if aircraft_id not in grouped_data:
            grouped_data[aircraft_id] = []
        grouped_data[aircraft_id].append(row)
    return grouped_data

def detect_turn_start_from_runway_24L(matrix, departures24L):
    # Identify the indices of relevant columns
    header = matrix[0]
    ra_idx = header.index('RA')  # Roll Angle
    heading_idx = header.index('HEADING')  # Heading
    tta_idx = header.index('TTA')  # True Track Angle
    ti_idx = header.index('TI')  # Aircraft Identifier
    lat_idx = header.index('LAT')  # Latitude
    lon_idx = header.index('LON')  # Longitude
    alt_idx = header.index('CorrectedAltitude')  # Corrected Altitude

    aircraft_data = group_by_aircraft_id(matrix[1:], ti_idx)

    # Dictionary to store the detected turn start for each aircraft
    aircraft_turns = {}

    # Process each aircraft separately
    for aircraft_id, rows in aircraft_data.items():
        if aircraft_id in departures24L:  # Ensure this aircraft is in departures from 24L
            last_valid_ra_row = None  # Last valid row with RA and TTA
            for i in range(len(rows)):
                current_row = rows[i]
                
                if current_row[alt_idx] < 50:
                    continue

                # Convert relevant values to numbers (handle "N/A")
                try:
                    ra = float(current_row[ra_idx].replace(',', '.')) if current_row[ra_idx] != 'N/A' else None
                    tta = float(current_row[tta_idx].replace(',', '.')) if current_row[tta_idx] != 'N/A' else None
                    heading = float(current_row[heading_idx].replace(',', '.'))
                except ValueError:
                    continue

                # If RA and TTA are available, compare with the last valid row
                if ra is not None and tta is not None:
                    if last_valid_ra_row:
                        try:
                            last_ra = float(last_valid_ra_row[ra_idx].replace(',', '.'))
                            last_tta = float(last_valid_ra_row[tta_idx].replace(',', '.'))
                        except ValueError:
                            continue

                        if (
                            abs(ra - last_ra) > 2 or  # Significant change in RA
                            abs(tta - last_tta) > 5   # Significant change in TTA
                        ):
                            lat = current_row[lat_idx]
                            lon = current_row[lon_idx]
                            alt = current_row[alt_idx]
                            aircraft_turns[aircraft_id] = (aircraft_id, lat, lon, alt)
                            break

                    # Update the last valid row with RA and TTA
                    last_valid_ra_row = current_row

                # If RA and TTA are not available, use Heading to detect the turn
                elif i > 0:  # Compare with the previous row
                    prev_row = rows[i - 1]
                    try:
                        prev_heading = float(prev_row[heading_idx].replace(',', '.'))
                    except ValueError:
                        continue

                    if abs(heading - prev_heading) > 5:  # Significant change in Heading
                        lat = current_row[lat_idx]
                        lon = current_row[lon_idx]
                        alt = current_row[alt_idx]
                        aircraft_turns[aircraft_id] = (aircraft_id, lat, lon, alt)
                        break  # Exit after detecting the first turn

    # Return the list with the results
    return [info for info in aircraft_turns.values()]

def side_of_line(p, p1, p2):
    return (p[1] - p1[1]) * (p2[0] - p1[0]) - (p[0] - p1[0]) * (p2[1] - p1[1])

def dms_to_decimal(degrees, minutes, seconds):
    return degrees + (minutes / 60) + (seconds / 3600)    

def crosses_fixed_radial(trajectories, matching_departures_24L):
    """ Determines if the trajectories of planes cross the 234 BCN radial  """

    # Coordenadas DVOR BCN
    lat_dvor_bcn = dms_to_decimal(41, 18, 25.6)
    lon_dvor_bcn = dms_to_decimal(2, 6, 28.1)

    # Coordenadas Punto en la línea de costa
    lat_punto_costas = dms_to_decimal(41, 16, 5.4)
    lon_punto_costas = dms_to_decimal(2, 2, 0.0)

    point1 = [lat_dvor_bcn, lon_dvor_bcn]
    point2 = [lat_punto_costas, lon_punto_costas] 
    

    results = {}

    for plane_id, trajectory in trajectories.items():
        if plane_id in matching_departures_24L:
            if len(trajectory) < 2:
                # If there are not enough points, the trajectory cannot cross the radial
                results[plane_id] = False
                continue
            
            crossed = False
            for i in range(len(trajectory) - 1):
                # Filtrar por puntos bajo 500 ft
                current_altitude = float(trajectory[i]['corrected_altitude'])
                next_altitude = float(trajectory[i + 1]['corrected_altitude'])

                if (current_altitude > 500 and next_altitude > 500) or current_altitude < 50:
                    continue  # Saltar si ambos puntos están por encima de 500 ft
                
                # Current and next point in the trajectory
                current_point = (float(trajectory[i]['latitude']), float(trajectory[i]['longitude']))
                next_point = (float(trajectory[i + 1]['latitude']), float(trajectory[i + 1]['longitude']))
                
                # Calculate the side of each point relative to the line
                side1 = side_of_line(current_point, point1, point2)
                side2 = side_of_line(next_point, point1, point2)
                
                # If the signs change, the trajectory crosses the radial
                if side1 * side2 < 0:
                    print(current_altitude)
                    crossed = True
                    break
            
            results[plane_id] = crossed

    return results

# Función para realizar la interpolación lineal
def interpolate_ias(alt1, alt2, ias1, ias2, target_altitude):
    if alt2 == alt1:  # Evitar la división por 0
        return ias1
    return ias1 + (ias2 - ias1) * (target_altitude - alt1) / (alt2 - alt1)


def extract_IAS_for_altitudes(data, altitudes=[850, 1500, 3500]):

    header = data[0]
    ti_idx = header.index('TI')
    alt_idx = header.index('CorrectedAltitude')
    ias_idx = header.index('IAS')

    aircraft_data = group_by_aircraft_id(data[1:], ti_idx)
    
    # Crear un diccionario para almacenar los resultados
    ias_values = {alt: [] for alt in altitudes}
    
    # Recorremos las aeronaves y sus datos
    for aircraft_id, rows in aircraft_data.items():
        for row in rows:
            # Obtener la altitud y manejar "N/A"
            altitude = row[alt_idx]
            if altitude != 'N/A':
                altitude = float(altitude)  # Convertir a float
            else:
                altitude = None

            # Obtener la velocidad IAS y manejar "N/A"
            ias = row[ias_idx]
            if ias != 'N/A':
                ias = float(ias.replace(',', '.'))  # Convertir a float
            else:
                ias = None

            # Para cada altitud de interés, si el avión ha alcanzado o superado esa altitud
            for target_altitude in altitudes:
                if altitude is not None and altitude >= target_altitude:
                    # Encontrar las dos alturas más cercanas a la altitud deseada
                    lower_altitude = None
                    upper_altitude = None
                    lower_ias = None
                    upper_ias = None
                    
                    # Buscar las dos alturas más cercanas
                    for comp_row in rows:
                        comp_altitude = float(comp_row[alt_idx]) if comp_row[alt_idx] != 'N/A' else None
                        comp_ias = float(comp_row[ias_idx].replace(',', '.')) if comp_row[ias_idx] != 'N/A' else None

                        if comp_altitude is not None:
                            # Si la altitud es menor o igual, puede ser la inferior
                            if comp_altitude <= target_altitude:
                                if lower_altitude is None or comp_altitude > lower_altitude:
                                    lower_altitude = comp_altitude
                                    lower_ias = comp_ias
                            # Si la altitud es mayor o igual, puede ser la superior
                            if comp_altitude >= target_altitude:
                                if upper_altitude is None or comp_altitude < upper_altitude:
                                    upper_altitude = comp_altitude
                                    upper_ias = comp_ias
                    
                    # Verificar si se encontraron las dos alturas cercanas
                    if lower_altitude is not None and upper_altitude is not None:
                        # Si se encuentran las dos alturas, realizar la interpolación
                        if lower_ias is not None and upper_ias is not None:
                            interpolated_ias = interpolate_ias(lower_altitude, upper_altitude, lower_ias, upper_ias, target_altitude)
                            # Almacenamos el resultado solo si no hemos registrado esta aeronave para esta altitud
                            if not any(aircraft_id == a[0]  for a in ias_values[target_altitude]):
                                ias_values[target_altitude].append((aircraft_id, interpolated_ias))
    
    return ias_values