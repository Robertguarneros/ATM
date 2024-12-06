# ATM Project
[Click here to use the app](https://atmproject.streamlit.app/)

## Project Structure
```
ATM/
│   .DS_Store
│   .flake8
│   .gitignore
│   Home.py
│   project.toml
│   README.md
│   requirements.txt
│   
├───assets
│   │   .DS_Store
│   │   logo_eurocontrol.png
│   │
│   ├───CsvFiles
│   │       P3_00-04h.csv
│   │       P3_04_08h.csv
│   │       P3_08_12h.csv
│   │       P3_12_16h.csv
│   │       P3_16_20h.csv
│   │       P3_20_24h.csv
│   │
│   └───InputFiles
│           2305_02_dep_lebl.xlsx
│           Tabla_Clasificacion_aeronaves.xlsx
│           Tabla_misma_SID_06R.xlsx
│           Tabla_misma_SID_24L.xlsx
│
├───functions
│       functions1.py
│       functions2.py
│       functions3.py
│
├───pages
|       General_Information.py
|       About.py
│       Altitude_and_IAS_at_runway_threshold.py
│       Horizontal_Distance_to_TMR-40.py
│       IAS_at_different_Altitudes.py
│       Position_and_Altitude_when_Turning.py
│       Radial_Crossing.py
│       Separation_Losses.py
```

## Objectives

- Show statistics about the separation between flights and wether or not the separation requirements are fulfilled.
    - Radar
    - Wake
    - Letter of Agreement
- Show statistics of the position and corrected altitude when the departure (from 24L) starts turning
- Show whether radial 234 is crossed when departing 
- Show IAS of departures at 850, 1500 and 3500 ft for both runways
- Altitude corrected and IAS of traffic at threshold when departing at 24L and 06R
- Horizontal (stereographical) distance from departures to TMR-40 when departing from 24L

### 1 David
- Separation between flights
    - Pasar a stereograficas
    - Funcion que regrese listas de vuelos consecutivos
    - Comparar distancias (hecha) y ver que cumplan:
        - Radar TMA solo tomar 1
        - Estela, usar fichero clasificación, espacio torre y TMA solo tomar 1
        - LoA espacio torre

### 2 Angela
- Función para saber si despega por la 24L o 06R
- Departures 24L
    - Función para saber si despega por la 24L o 06R
    - Detectar que inica el viraje (usar Roll Angle, Heading y True Track Angle)
    - Position and altitude corrected where turn starts when departing from 24L
    - Mirar si durante el despegue ha cruzado el radial 234 DVOR-DME BCN
- IAS of departures at 850, 1500 and 3500 ft for both runways

### 3 Roberto 
- Mirar las coordenadas del threshold de cada pista
- Altitude corrected and IAS of traffic at threshold when departing at 24L and 06R
    - Conversion with 
'''python
def dms_to_decimal(degrees, minutes, seconds, direction):
    decimal = degrees + (minutes / 60) + (seconds / 3600)
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal
'''
    - 06R 411656.32N, 0020427.66E Latitude: 41.28231111111111, Longitude: 2.0743500000000004
    - 24L 411731.99N, 0020611.81E Latitude: 41.29221944444444, Longitude: 2.1032805555555556
- Horizontal distance stereographical from departures to TMR-40 (41,27194444440, 2,04777777778) por 24L

## Functions

### Miscellaneous functions
These are functions we use repeatedly within our calculations:
- `load_departures`: this function is in charge of loading the excel contaning the departure list and returns a list of the departures.
- `load_flights`: this function is in charge of loading the `csv` files that contain the flight data. It returns a matrix with the data.
- `load_24h`: this function is in charge of loading all the `csv` files to be able to view data for 24 hours. It returns a matrix with the data.
- `corrected_altitude`: this function is used to get the corrected altitude by receiving the barometric pressure setting and the flight level information. It returns the corrected altitude in feet.
- `get_stereographical_from_lat_lon_alt`: this function helps us convert the coordinates to stereographical, it has three subfunctions which are self explanatory:
    - `geodesic_to_geocentric`
    - `geocentric_to_system_cartesian`
    - `system_cartesian_to_system_stereographical`

### Separation between flights
Explain
### Position and Altitude turns
Explain
### Radial Crossing
Explain
### IAS at different altitudes
Explain
### Altitude and IAS at threshold
This function is composed of multiple smaller functions that together achieve the goal of getting the corrected altitude and IAS when crossing the threshold of the runway. The order of these functions is:
- `load_departures`: to load the departures.
- `load_flights`: to load only the time frame the user wants to see.
- `load_24h`: to load the whole day and allow the user to view all data.
- `filter_departures_by_runway`: this function returns a list containing the identifiers of the flights that depart from 24L and another list for 06R.
- `correct_altitude_for_file`: this function is called to get the corrected altitdue for the whole matrix and not just one flight, it uses function `corrected_altitude` described previously.
- `get_trajectory_for_airplane`: this function takes the matrix of flights and makes a dictionary that has the flight ID and within, the coordinates of the trajectory. This allows us to quickly interpolate or plot trajectories since the data for one flight is already in one place and not spread.
- `filter_empty_trajectories`: this function filters any flight that might be empty.
- `interpolate_trajectories`: this function helps us interpolate the coordinates, in our case we decided to use an interpolation of the position, velocity and corrected altitude every 0.5 seconds. This is because we wanted to achieve a high precision of detections.
- `filter_trajectories_by_runway`: this function divides the filtered trajectories by runway so we can show data separately. 
- `get_corrected_altitude_and_ias_at_threshold`: this function is the one in charge of detecting when a flight crosses the threshold, we decided to go with the area approach for maximum precision. The coordinates we used were the following:

```python
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
```

The flow of the function would look like this:
```mermaid
flowchart TD
    A[Start] -->B(load_departures)
    B --> C(load_flights)
    C --> D(load_24h)
    D --> E(filter_departures_by_runway)
    E --> F(correct_altitude_for_file)
    F --> G(get_trajectory_for_airplane)
    G --> H(filter_empty_trajectories)
    H --> I(interpolate_trajectories)
    I --> J(filter_trajectories_by_runway)
    J --> K(get_corrected_altitude_and_ias_at_threshold)
    K --> L(End)
```

### Horizontal distance to TMR-40
Explain

## For Developers
### First time installing Project
1. Clone repo: `git clone https://github.com/Robertguarneros/ATM.git`
2. Change into the project directory 
3. Install the dependencies: `pip install -r requirements.txt`
4. Run proyect with `streamlit run .\Home.py`

### Project Structure

The source code of the project is organized as follows:

- `assets`: contains logo and images used.
- `App.py`: entry point of the app, also where all the GUI menu elements and functions are defined.
 
### Libraries
The main Python libraries used were:
- streamlit

### Tools Used

We are also using the following tools:
- `isort`: to order imports alphabetically, use with `isort .`
- `black`: formatter, use with `black .`
- `flake8`: linting tool, use with `flake8 .`


### Requirements
To generate requirement list use:
`pip freeze > requirements.txt`

#### Install Requirements

The requirements can be installed from the requirements.txt file:
`pip install -r requirements.txt`

#### Verify Requirements
`pip list`