Welcome!
This repository contains the code developed for the master thesis degree of the course ICT for Smart Societies at the Politecnico di Torino.
The project consists of a pipeline whose main goal is the one of outputting a cityJSON file (for further conversion to CityGML) storing buildings data, compliant
with the extensions schemas for Energy and Utility Network developed according the respective cityGML Application Domain Extensions (ADEs) specifications. 

To be started, please follow the reverse path from the inner folder ("buildings/file_loader") to the outer one.
The scripts to be run are respectively:

1) buildings/file_loader/loader.py;
2) buildings/main.py;
3) to_cj.py.

But first, for each one of the step listed above, the user is required to follow the configuration steps in-depth explained in the README.md file inside each working directory,
except for the current repo, where you can find the specifications for the last configuration steps for correctly running to_cj.py in LAST_STEP.md.
Please, follow them carefully for correctly obtaining the wished output.

Notice that the whole pipeline has been designed for an italian study case, relying on external files to be provided.
Especially for utility network data, just for testing purposes, the ding0 tool (https://github.com/openego/ding0) has been run over a german database, 
but the final output relies on network data externally provided as pandapower file.

A virtual environment creation is strongly suggested. The needed packages are:

chardet
geopy
geopandas
matplotlib
openpyxl
osmnx
pandapower
pandas
pyproj
requests
rtree
scipy
shapely

Feel free to use, update and add features to the developed code according to your purposes. 
Do not hesitate in contacting us for any further clarifications.

