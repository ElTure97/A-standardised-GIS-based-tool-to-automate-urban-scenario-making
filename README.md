Welcome! 

This repository contains the code developed for the ICT for Smart Societies master's degree thesis at the Politecnico di Torino, titled:

"A standardised GIS-based tool to automate urban scenario making for co-simulation of multi-energy systems"

The project consists of a pipeline whose primary goal is to output a CityJSON file (for further conversion to CityGML) storing buildings' data, compliant
with the extensions' schemas for Energy and Utility Network developed according to the respective CityGML Application Domain Extensions (ADEs) specifications. 

To start, please follow the reverse path from the inner folder ("buildings/file_loader") to the outer one to correctly set the instance.
The configuration steps are explained in the corresponding .md file inside each working directory.
Please follow them carefully to obtain the desired output. 
The scripts to be run are, respectively:

1) buildings/file_loader/loader.py;
2) buildings/main.py;
3) to_cj.py.

But actually, the project has been designed such that only "to_cj.py" must be run by following the instructions displayed on the terminal.

You can also check the pipeline diagram in the current repository to better understand how the application works.

Notice that the whole pipeline has been designed for an Italian study case, relying on external files to be provided.
Utility network data, just for testing purposes during development, have been achieved through the ding0 tool (https://github.com/openego/ding0), which, at the time of writing, works ONLY over a German database. 
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
Do not hesitate to contact us for any further clarifications!

