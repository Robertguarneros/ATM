# ATM Project

## Objectives
- Separation between flights
    - Radar
    - Estela
    - LoA 
- Position and altitude where place starts turn when departing from 24L
- Radial from DVOR-DME BCN that crosses the turn when departing from 24L
- IAS of departures at 850, 1500 and 3500 ft for both runways??
- Altitude and velocity of traffic at threshold when departing at 24L and 06R
- Horizontal distance from departures to TMR-40 (41,27194444440, 2,04777777778)

### Separation between flights



## For Developers
### First time installing Project
1. Clone repo: `git clone https://github.com/Robertguarneros/AsterixProject.git`
2. Change into the project directory 
3. Install the dependencies: `pip install -r requirements.txt`
4. Run proyect

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


### To create Executable
- List dependencies with `pip install -r requirements.txt`
- `pip install pyinstaller`
- `pyinstaller --onefile --noconsole --add-data "map.html;." --add-data "UserManual.pdf;." --add-data "assets;assets" App.py`
- The executable will be generated in the `dist` directory.
