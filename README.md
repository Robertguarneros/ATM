# ATM Project
[Click here to use the app](https://atmproject.streamlit.app/)
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
- Altitude corrected and velocity of traffic at threshold when departing at 24L and 06R
- Horizontal distance stereographical from departures to TMR-40 (41,27194444440, 2,04777777778) por 24L


## Example
df_reshaped = pd.read_csv('data/us-population-2010-2019-reshaped.csv')

### Separation between flights



## For Developers
### First time installing Project
1. Clone repo: `git clone https://github.com/Robertguarneros/ATM.git`
2. Change into the project directory 
3. Install the dependencies: `pip install -r requirements.txt`
4. Run proyect with `streamlit run app.py`

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