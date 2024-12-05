# ATM Project
[Click here to use the app](https://atmapp.streamlit.app/)

## Project Structure
```
ATM/
│   .DS_Store
│   .flake8
│   .gitignore
│   home_page.py
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
│       Altitude_and_IAS_at_runway_threshold.py
│       Horizontal_Distance_to_TMR-40.py
│       IAS_at_different_Altitudes.py
│       Position_and_Altitude_when_Turning.py
│       Radial_Crossing.py
│       Separation_Losses.py
```

## Objectives

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


## Example
df_reshaped = pd.read_csv('data/us-population-2010-2019-reshaped.csv')

### Separation between flights



## For Developers
### First time installing Project
1. Clone repo: `git clone https://github.com/Robertguarneros/ATM.git`
2. Change into the project directory 
3. Install the dependencies: `pip install -r requirements.txt`
4. Run proyect with `streamlit run .\home_page.py`

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