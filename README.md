Welcome!
This repository contains the code developed for the master's degree thesis of the course ICT for Smart Societies at the Politecnico di Torino.
The project consists of a pipeline whose main goal is to output a CityJSON file (for further conversion to CityGML) storing buildings data, compliant
with the extensions schemas for Energy and Utility Network developed according to the respective CityGML Application Domain Extensions (ADEs) specifications. 

To be started, please follow the reverse path from the inner folder ("buildings/file_loader") to the outer one.
The scripts to be run are respectively:

1) buildings/file_loader/loader.py;
2) buildings/main.py;
3) to_cj.py.

They can also be used as methods, but first, for each one of the steps listed above, the user is required to follow the configuration steps in-depth explained in the corresponding .md file inside each working directory.
Please, follow them carefully for correctly obtaining the wished output. 

You can also check the pipeline diagram you find in the current repository for better displaying how the application works.

Notice that the whole pipeline has been designed for an Italian study case, relying on external files to be provided.
Utility network data, just for testing purposes during development, have been achieved through the ding0 tool (https://github.com/openego/ding0) which at the time of writing works ONLY over a German database. 
Instead, the final output relies on network data externally provided as PandaPower file.

A virtual environment creation is strongly suggested. The needed packages are:

- chardet;
- geopy;
- geopandas;
- matplotlib;
- openpyxl;
- osmnx;
- pandapower;
- pandas;
- pyproj;
- requests;
- rtree;
- scipy;
- shapely.

Feel free to use, update and add features to the developed code according to your purposes. 
Do not hesitate in contacting us for any further clarifications!

