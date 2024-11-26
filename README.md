# ATM Project

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
- math
- webbrowser
- PyQt5
- numpy
- csv
- OpenStreetMap
- Leaflet

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
