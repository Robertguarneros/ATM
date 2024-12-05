import csv

import numpy as np
import pandas as pd

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



# Insert corrected altitude for a file at the last column
def correct_altitude_for_file(matrix):
    # Add a column that has the corrected altitude
    # Find the column indices for BP (Barometric Pressure) and FL (Flight Level)
    bp_index = matrix[0].index("BP")
    fl_index = matrix[0].index("FL")

    # Check if "CorrectedAltitude" already exists in the header
    if "CorrectedAltitude" not in matrix[0]:
        matrix[0].append("CorrectedAltitude")  # Append the header for the corrected altitude

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


def filter_departures_by_runway(departures_matrix, flights_matrix):
    # Returns a list of TIs corresponding to a runway
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


def trajectories_to_stereographical(filtered_trajectories):
    # Initialize the new dictionary for stereographical coordinates
    stereographical_trajectories = {}

    # Iterate through each flight and its trajectory points
    for flight_id, points in filtered_trajectories.items():
        stereographical_points = []
        for point in points:
            # Extract latitude, longitude, and height from the trajectory point
            lat = float(point["latitude"])
            lon = float(point["longitude"])
            alt = float(point["height"])

            # Convert to stereographical coordinates
            res = get_stereographical_from_lat_lon_alt(lat, lon, alt)

            # Append the transformed point to the flight's trajectory
            stereographical_points.append(
                {
                    "U": float(res["U"]),
                    "V": float(res["V"]),
                    # "Height": res["Height"]
                }
            )

        # Store the transformed trajectory for this flight
        stereographical_trajectories[flight_id] = stereographical_points

    return stereographical_trajectories


def calculate_min_distance_to_TMR_40_24L(stereographical_trajectories, departures_24L):
    """
    Calculate the minimum distance to TMR-40 for flights departing from 24L.

    Args:
        stereographical_trajectories (dict): A dictionary where keys are flight IDs and
                                             values are lists of (U, V) trajectory points.
        departures_24L (list): A list of flight IDs departing from 24L.

    Returns:
        dict: A dictionary where keys are flight IDs and values are the minimum distance to TMR-40.
    """
    # Stereographical coordinates of TMR-40
    TMR_U = 68775.90421516102
    TMR_V = 18416.232324621615

    # Filter trajectories for flights in departures_24L
    filtered_trajectories = {
        flight_id: points
        for flight_id, points in stereographical_trajectories.items()
        if flight_id in departures_24L
    }

    # Dictionary to store the minimum distances
    min_distances = {}

    # Calculate the minimum distance for each filtered trajectory
    for flight_id, trajectory_points in filtered_trajectories.items():
        distances = [
            calculate_distance(float(point["U"]), float(point["V"]), TMR_U, TMR_V)
            for point in trajectory_points
        ]
        # Store the minimum distance
        min_distances[flight_id] = min(distances)

    return min_distances  # In nautical miles


def load_files(departures_file, flights_file):
    loaded_departures = load_departures(departures_file)
    loaded_flights = load_flights(flights_file)
    return loaded_departures, loaded_flights

def calculate_min_distance_to_TMR_40_24L_global(loaded_departures,loaded_flights):
    corrected_alitude_matrix = correct_altitude_for_file(loaded_flights)    
    trajectories = get_trajectory_for_airplane(loaded_departures, corrected_alitude_matrix)
    filtered_trajectories = filter_empty_trajectories(trajectories)
    stereographical_trajectories = trajectories_to_stereographical(filtered_trajectories)
    departures_6R, departures_24L = filter_departures_by_runway(
        loaded_departures, loaded_flights
    )
    minimum_distances = calculate_min_distance_to_TMR_40_24L(stereographical_trajectories, departures_24L)
    return minimum_distances # Returns a dictionary with the flight identifier and the minimum distance in NM


def filter_trajectories_by_runway(stereographical_trajectories, departures_24L, departures_6R):
    # Returns two list, one for each runway contaning the flight and the respective trajectories.
    # Filter trajectories for flights in departures_24L
    filtered_trajectories_024L = {
        flight_id: points
        for flight_id, points in stereographical_trajectories.items()
        if flight_id in departures_24L
    }
     # Filter trajectories for flights in departures_06R
    filtered_trajectories_06R = {
        flight_id: points
        for flight_id, points in stereographical_trajectories.items()
        if flight_id in departures_6R
    }
    return filtered_trajectories_024L, filtered_trajectories_06R


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

            # Create new time range (0.5-second intervals)
            interpolated_times = np.arange(original_times[0], original_times[-1] + 0.5, 0.5)

            # Interpolate latitude, longitude, altitude, and corrected altitude
            interpolated_latitudes = np.interp(interpolated_times, original_times, latitudes)
            interpolated_longitudes = np.interp(interpolated_times, original_times, longitudes)
            interpolated_altitudes = np.interp(interpolated_times, original_times, altitudes)
            interpolated_corrected_altitudes = np.interp(interpolated_times, original_times, corrected_altitudes)
            interpolated_ias = np.interp(interpolated_times, original_times, ias)

            # Create interpolated trajectory points
            interpolated_points = []
            for i, t in enumerate(interpolated_times):
                interpolated_points.append({
                    "time": t,
                    "latitude": interpolated_latitudes[i],
                    "longitude": interpolated_longitudes[i],
                    "height": interpolated_altitudes[i],
                    "corrected_altitude": interpolated_corrected_altitudes[i],
                    "ias": interpolated_ias[i]
                })

            # Store the interpolated trajectory for this flight
            interpolated_trajectories[flight_id] = interpolated_points
        except Exception as e:
            print(f"Error interpolating trajectory for flight {flight_id}: {e}")

    return interpolated_trajectories

# Set a threshold
# Check for every flight, the time at which it crosses said threshold
# Record the callsign, IAS and corrected altitude at that time for that flight
# Store them in a vector, one for 24L and one for 06R 
# Keep in mind some flights will never appear due to turning earlier
# Keep in mind the percentage of flights that cross and dont cross over the total flights in the vector
# Show data as distribution by time, type of aircraft, SID, company, etc.
# Show statistics


def get_corrected_altitude_and_ias_at_threshold(interpolated_trajectories_024L, interpolated_trajectories_06R):
    """
    Records the flight ID, corrected altitude, and IAS of traffic when crossing the runway threshold areas.

    Args:
        interpolated_trajectories_024L (dict): Interpolated trajectories for flights at 24L.
        interpolated_trajectories_06R (dict): Interpolated trajectories for flights at 06R.

    Returns:
        dict: A dictionary with runway names as keys and a list of dictionaries
              containing flight ID, corrected altitude, and IAS as values.
    """
    # Define threshold areas as bounding boxes
    threshold_06R_area = {
        "min_lat": 41.291979,  # Bottom latitude
        "max_lat": 41.293154,  # Top latitude
        "min_lon": 2.103089,   # Left longitude
        "max_lon": 2.105704    # Right longitude
    }
    threshold_24L_area = {
        "min_lat": 41.281430,  # Bottom latitude
        "max_lat": 41.282578,  # Top latitude
        "min_lon": 2.072046,   # Left longitude
        "max_lon": 2.074564    # Right longitude
    }

    # Function to check if a point is within an area
    def is_within_area(lat, lon, area):
        return (
            area["min_lat"] <= lat <= area["max_lat"]
            and area["min_lon"] <= lon <= area["max_lon"]
        )

    # Initialize results
    results = {
        "24L": [],
        "06R": []
    }

    
    # Process flights for 24L
    for flight_id, points in interpolated_trajectories_024L.items():
        for point in points:
            lat, lon = float(point["latitude"]), float(point["longitude"])

            if is_within_area(lat, lon, threshold_24L_area):
                results["24L"].append({
                    "time": point["time"],
                    "flight_id": flight_id,
                    "corrected_altitude": point["corrected_altitude"],
                    "ias": point["ias"]
                })
                break  # Exit loop after first match for this flight

    # Process flights for 06R
    for flight_id, points in interpolated_trajectories_06R.items():
        for point in points:
            lat, lon = float(point["latitude"]), float(point["longitude"])

            if is_within_area(lat, lon, threshold_06R_area):
                results["06R"].append({
                    "time": point["time"],
                    "flight_id": flight_id,
                    "corrected_altitude": point["corrected_altitude"],
                    "ias": point["ias"]
                })
                break  # Exit loop after first match for this flight

    return results




def get_corrected_altitude_and_ias_at_threshold_global(loaded_departures,loaded_flights):
    departures_6R, departures_24L = filter_departures_by_runway(loaded_departures, loaded_flights)
    corrected_alitude_matrix = correct_altitude_for_file(loaded_flights)    
    trajectories = get_trajectory_for_airplane(loaded_departures, corrected_alitude_matrix)
    filtered_trajectories = filter_empty_trajectories(trajectories)
    interpolated_trajectories = interpolate_trajectories(filtered_trajectories)
    filtered_trajectories_024L, filtered_trajectories_06R = filter_trajectories_by_runway(interpolated_trajectories, departures_24L, departures_6R)
    results = get_corrected_altitude_and_ias_at_threshold(filtered_trajectories_024L, filtered_trajectories_06R)
    return results