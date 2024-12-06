import csv

import numpy as np
import pandas as pd
from datetime import datetime

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

# Load flight data
def load_24h(file1, file2, file3, file4, file5, file6):
    # Initialize an empty matrix to hold all data
    matrix = []
    first_file = True  # Flag to indicate if it's the first file being processed

    for file in [file1, file2, file3, file4, file5, file6]:
        with open(file, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            
            # Skip the header for all files except the first
            if not first_file:
                next(reader, None)  # Skip the header row
            else:
                first_file = False  # Ensure subsequent files skip the header

            # Generate a matrix by reading all rows
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
    ra_idx = loaded_flights[0].index('RA')  # Roll Angle
    heading_idx = loaded_flights[0].index('HEADING')  # Heading
    tta_idx = loaded_flights[0].index('TTA')  # True Track Angle
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
            ra = row[ra_idx]
            tta = row[tta_idx]
            heading = row[heading_idx]
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
                        "ra": ra,
                        "tta": tta,
                        "heading": heading,
                        "corrected_altitude": corrected_altitude,
                        "ias": ias,
                    }
                )
            

    return trajectories

def filter_empty_trajectories(trajectories):
    # Create a new dictionary containing only flights with non-empty trajectories
    filtered_empty_trajectories = {
        flight_id: points
        for flight_id, points in trajectories.items()
        if points  # Keep only if the points list is not empty
    }
    return filtered_empty_trajectories

def filter_trajectories_24L(interpolated_trajectories, departures_24L):
    # Filtrar las trayectorias basadas en las pistas
    filtered_trajectories_24L = {}

    # Iterar sobre las trayectorias filtradas por vuelo
    for flight_id, trajectory in interpolated_trajectories.items():

        if flight_id in [x[0] for x in departures_24L]:  # Salidas en pista 24L
            # Filtrar la trayectoria para que el tiempo de cada punto sea <= 5 minutos antes de la hora de despegue
            departure_time = next((row[1] for row in departures_24L if row[0] == flight_id), None)
            if departure_time:

                # Filtrar los puntos de la trayectoria
                filtered_trajectory = []
                for point in trajectory:
                    trajectory_time = float(point['time'])  # Suponiendo que el tiempo está en segundos
                    # Comprobar si el tiempo de la trayectoria está al menos 5 minutos antes del tiempo de despegue
                    if departure_time - 300 <= trajectory_time <= departure_time + 100:
                        filtered_trajectory.append(point)

                # Almacenar la trayectoria filtrada
                if filtered_trajectory:
                    filtered_trajectories_24L[flight_id] = filtered_trajectory

    return filtered_trajectories_24L
    

def filter_departures_by_runway(departures_matrix, flights_matrix):
    # Returns a list of TIs corresponding to a runway
    # Get the header row for each matrix
    departures_header = departures_matrix[0]
    flights_header = flights_matrix[0]

    # Find the index of relevant columns in the departures matrix
    pista_desp_index = departures_header.index('PistaDesp')
    indicativo_index = departures_header.index('Indicativo')
    time_departure_index = departures_header.index('HoraDespegue')

    # Find the index of relevant columns in the flights matrix
    ta_index = flights_header.index('TI')
    time_index = flights_header.index('TIME(s)')

    reference_time = float(flights_matrix[1][time_index])

    # Create a set of all flight identifiers (TI) for quick lookup
    flight_ti_set = {row[ta_index] for row in flights_matrix[1:]}

    # Initialize lists to store matching departures
    matching_departures_6R = []
    matching_departures_24L = []

    # Process the departures matrix once
    for row in departures_matrix[1:]:
        indicativo = row[indicativo_index]
        pista_desp = row[pista_desp_index]
        hora_despegue_str = str(row[time_departure_index])
        dt = datetime.strptime(hora_despegue_str, "%Y-%m-%d %H:%M:%S")
        hora_despegue = round(dt.hour * 3600 + dt.minute * 60 + dt.second)

        # Check if the flight matches a TI in the flights matrix
        if indicativo in flight_ti_set:
            if(hora_despegue >= reference_time):
                if pista_desp == 'LEBL-06R':
                    # Store indicativo and hora_despegue as a tuple
                    matching_departures_6R.append((indicativo, hora_despegue))
                elif pista_desp == 'LEBL-24L':
                    # Store indicativo and hora_despegue as a tuple
                    matching_departures_24L.append((indicativo, hora_despegue))

    return matching_departures_6R, matching_departures_24L


def detect_turn_start_from_runway_24L(interpolated_trajectories):
    # Dictionary to store the detected turn start for each aircraft
    aircraft_turns = {}

    # Iterate over each aircraft in the interpolated trajectories
    for aircraft_id, rows in interpolated_trajectories.items():
        if len(rows) < 4:  # Ensure there are enough points to compare
            continue
        
        heading_change_accumulated = 0  # To accumulate heading changes
        roll_angle_change_accumulated = 0  # To accumulate roll angle changes
        tta_change_accumulated = 0  # To accumulate TTA changes
        detected_turn = False  # Flag to check if the turn has been detected

        for i in range(1, len(rows)):
            current_row = rows[i]

            # Skip if the altitude is too low (indicating the aircraft is still on the ground)
            if float(current_row['corrected_altitude']) < 390:
                continue

            try:
                ra = float(current_row['ra'])  # Roll angle
                tta = float(current_row['tta'])  # Turn-To Angle
                heading = float(current_row['heading'])  # Heading
            except ValueError:
                continue

            # Checking for significant change in heading, roll angle and TTA
            if i >= 4:  # Only start comparing after 4 points (2 seconds)
                prev_row = rows[i - 4]  # Get the previous data point (2 seconds before)
                
                try:
                    prev_ra = float(prev_row['ra'])
                    prev_tta = float(prev_row['tta'])
                    prev_heading = float(prev_row['heading'])
                except ValueError:
                    continue

                # Accumulating the changes
                heading_change = abs(heading - prev_heading)
                roll_angle_change = abs(ra - prev_ra)
                tta_change = abs(tta - prev_tta)

                # Accumulate the changes over time
                heading_change_accumulated += heading_change
                roll_angle_change_accumulated += roll_angle_change
                tta_change_accumulated += tta_change

                # Check if the accumulated change exceeds a certain threshold
                if (heading_change_accumulated > 8 or  # Total accumulated heading change over time
                    roll_angle_change_accumulated > 5 or  # Total accumulated roll angle change
                    tta_change_accumulated > 15):  # Total accumulated TTA change
                    # The aircraft has started the turn
                    lat = current_row['latitude']
                    lon = current_row['longitude']
                    alt = current_row['corrected_altitude']
                    aircraft_turns[aircraft_id] = (aircraft_id, lat, lon, alt)
                    detected_turn = True
                    break  # We found the first point where the turn starts

        # If no turn was detected, add the aircraft to the results with None
        if not detected_turn:
            aircraft_turns[aircraft_id] = None

    # Return the list with the results
    return [info for info in aircraft_turns.values()]


def side_of_line(p, p1, p2):
    return (p[1] - p1[1]) * (p2[0] - p1[0]) - (p[0] - p1[0]) * (p2[1] - p1[1])

def dms_to_decimal(degrees, minutes, seconds):
    return degrees + (minutes / 60) + (seconds / 3600)    

def crosses_fixed_radial(trajectories):
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
        if len(trajectory) < 2:
            # If there are not enough points, the trajectory cannot cross the radial
            results[plane_id] = False
            continue
        
        crossed = False
        for i in range(len(trajectory) - 1):
            # Filtrar por puntos bajo 500 ft
            current_altitude = float(trajectory[i]['corrected_altitude'])
            next_altitude = float(trajectory[i + 1]['corrected_altitude'])

            if current_altitude < 50:
                continue  
            
            # Current and next point in the trajectory
            current_point = (float(trajectory[i]['latitude']), float(trajectory[i]['longitude']))
            next_point = (float(trajectory[i + 1]['latitude']), float(trajectory[i + 1]['longitude']))

            # Calculate the side of each point relative to the line
            side1 = side_of_line(current_point, point1, point2)
            side2 = side_of_line(next_point, point1, point2)
                
            # If the signs change, the trajectory crosses the radial
            if side1 * side2 < 0:
                crossed = True
                break
            
        results[plane_id] = crossed

    return results

def interpolate_trajectories(filtered_trajectories):
    """
    Interpolate flight trajectories to every 0.5 seconds, including corrected altitude.

    Args:
        filtered_trajectories (dict): A dictionary where keys are flight IDs and
                                      values are lists of trajectory points with time, latitude,
                                      longitude, height, and corrected altitude.

    Returns:
        dict: A dictionary where keys are flight IDs and values are interpolated trajectory points.
    """
    interpolated_trajectories = {}

    for flight_id, points in filtered_trajectories.items():
        if len(points) < 2:
            # Skip flights with less than 2 points (cannot interpolate)
            continue
        
        try:
            # Extract original times and trajectory values
            original_times = np.array([float(point["time"]) for point in points])
            latitudes = np.array([float(point["latitude"]) for point in points])
            longitudes = np.array([float(point["longitude"]) for point in points])
            altitudes = np.array([float(point["height"]) for point in points])
            corrected_altitudes = np.array([float(point["corrected_altitude"]) for point in points])
            ias = np.array([float(point["ias"]) for point in points])
            heading = np.array([float(point["heading"]) for point in points])

            # Extract the RA and TTA, handling missing values (every 16s only)
            ra = np.array([float(point["ra"]) if point["ra"] != "N/A" else np.nan for point in points])
            tta = np.array([float(point["tta"]) if point["tta"] != "N/A" else np.nan for point in points])

            # Identify the indices where `ra` and `tta` are valid
            valid_indices = ~np.isnan(ra)
            valid_times_ra_tta = original_times[valid_indices]
            valid_ra = ra[valid_indices]
            valid_tta = tta[valid_indices]

            # Create new time range (0.5-second intervals)
            interpolated_times = np.arange(original_times[0], original_times[-1] + 0.5, 0.5)

            # Interpolate latitude, longitude, altitude, and corrected altitude
            interpolated_latitudes = np.interp(interpolated_times, original_times, latitudes)
            interpolated_longitudes = np.interp(interpolated_times, original_times, longitudes)
            interpolated_altitudes = np.interp(interpolated_times, original_times, altitudes)
            interpolated_corrected_altitudes = np.interp(interpolated_times, original_times, corrected_altitudes)
            interpolated_ias = np.interp(interpolated_times, original_times, ias)
            interpolated_heading = np.interp(interpolated_times, original_times, heading)

            # Interpolate RA and TTA only between valid times
            interpolated_ra = np.interp(interpolated_times, valid_times_ra_tta, valid_ra)
            interpolated_tta = np.interp(interpolated_times, valid_times_ra_tta, valid_tta)

            # Create interpolated trajectory points
            interpolated_points = []
            for i, t in enumerate(interpolated_times):
                interpolated_points.append({
                    "time": t,
                    "latitude": interpolated_latitudes[i],
                    "longitude": interpolated_longitudes[i],
                    "height": interpolated_altitudes[i],
                    "corrected_altitude": interpolated_corrected_altitudes[i],
                    "ias": interpolated_ias[i],
                    "heading": interpolated_heading[i],
                    "ra": interpolated_ra[i],
                    "tta": interpolated_tta[i]
                })

            # Store the interpolated trajectory for this flight
            interpolated_trajectories[flight_id] = interpolated_points
        except Exception as e:
            print(f"Error interpolating trajectory for flight {flight_id}: {e}")

    return interpolated_trajectories

# Función para realizar la interpolación lineal
def interpolate_ias(alt1, alt2, ias1, ias2, target_altitude):
    if alt2 == alt1:  # Evitar la división por 0
        return ias1
    return ias1 + (ias2 - ias1) * (target_altitude - alt1) / (alt2 - alt1)

def extract_IAS_for_altitudes(interpolated_trajectories, altitudes=[850, 1500, 3500]):
    
    # Crear un diccionario para almacenar los resultados
    ias_values = {alt: [] for alt in altitudes}
    
    # Recorremos las aeronaves y sus datos
    for aircraft_id, trajectory in interpolated_trajectories.items():
        for target_altitude in altitudes:
            # Variables para encontrar las dos altitudes más cercanas
            lower_altitude = None
            upper_altitude = None
            lower_ias = None
            upper_ias = None
            
            # Buscar las dos alturas más cercanas en la trayectoria
            for point in trajectory:
                altitude = float(point['corrected_altitude'])
                ias = float(point['ias']) if point['ias'] != 'N/A' else None

                if altitude == target_altitude:
                    if not any(aircraft_id == a[0] for a in ias_values[target_altitude]):
                        ias_values[target_altitude].append((aircraft_id, ias))

                elif altitude <= target_altitude:
                    if lower_altitude is None or altitude > lower_altitude:
                        lower_altitude = altitude
                        lower_ias = ias
                elif altitude >= target_altitude:
                    if upper_altitude is None or altitude < upper_altitude:
                        upper_altitude = altitude
                        upper_ias = ias

            # Si se encontraron las dos altitudes más cercanas, realizar interpolación
            if lower_altitude is not None and upper_altitude is not None:
                if lower_ias is not None and upper_ias is not None:
                    interpolated_ias = interpolate_ias(lower_altitude, upper_altitude, lower_ias, upper_ias, target_altitude)
                    # Almacenar el resultado si aún no se registró para esta aeronave
                    if not any(aircraft_id == a[0] for a in ias_values[target_altitude]):
                        ias_values[target_altitude].append((aircraft_id, interpolated_ias))

    return ias_values

def extract_IAS(loaded_departures, loaded_flights):
    flights = correct_altitude_for_file(loaded_flights)
    departures_6R, departures_24L = filter_departures_by_runway(loaded_departures, flights)
    trajectories = get_trajectory_for_airplane(loaded_departures, flights)
    filtered_trajectories = filter_empty_trajectories(trajectories)
    interpolated_trajectories = interpolate_trajectories(filtered_trajectories)
    ias = extract_IAS_for_altitudes(interpolated_trajectories, altitudes=[850, 1500, 3500])
    ias_06R = {alt: [] for alt in [850, 1500, 3500]}
    ias_24L = {alt: [] for alt in [850, 1500, 3500]}
    
    # Classify the aircraft based on the departure runway (6R or 24L)
    for altitude in [850, 1500, 3500]:
        for aircraft_id, ias_value in ias[altitude]:
            # Check if the aircraft is departing from runway 6R and add its IAS value to ias_06R
            if aircraft_id in [x[0] for x in departures_6R]:
                ias_06R[altitude].append((aircraft_id, ias_value))
            # Check if the aircraft is departing from runway 24L and add its IAS value to ias_24L
            elif aircraft_id in [x[0] for x in departures_24L]:
                ias_24L[altitude].append((aircraft_id, ias_value))

    # Return the classified IAS values for runway 6R and runway 24L
    return ias_06R, ias_24L

def extract_turn(loaded_departures, loaded_flights):
    f = correct_altitude_for_file(loaded_flights)
    trajectories_departures_24L = trajectories_turn_24L(f,loaded_departures)
    interpolated_trajectories = interpolate_trajectories(trajectories_departures_24L)
    turns = detect_turn_start_from_runway_24L(interpolated_trajectories)
    return turns

def trajectories_turn_24L(loaded_flights, loaded_departures):
    departures_06R, departures_24L = filter_departures_by_runway(loaded_departures, loaded_flights)
    trajectories = get_trajectory_for_airplane(loaded_departures, loaded_flights)
    empty_trajectories = filter_empty_trajectories(trajectories)
    trajectories_departures_24L = filter_trajectories_24L(empty_trajectories, departures_24L)

    return trajectories_departures_24L
