Welcome

Here there are listed the step to be followed to correctly use this application.
The configuration must be properly done only setting the value of fields in the file config/config.json:

1) First, you must specify the address around which you want to build your bounding box in the following format:
        address, CAP, City XX, Country ;
2) You have also to specify the size of the bounding box by expressing the distance (in meters) from the previously specified address and the desired resolution for elevation data mapping after the bounding box has been split in a grid.;
Please take care to adequately set the resolution since the elevation is obtained through HTTP get request to open elevation API which supports at most 512 locations per single request.
Then the resolution according to which the bounding box is discretized, must be choosen in order to not exceed this number.
3) Also, the city of interest must be specified properly filling the fields "provincia", "comune", "nation" and "h_slm" with the corresponding city height value (with respect to the sea level) as integer;
4) Following, the fields "NUTS3" and "LAU2" must be filled respectively with strings corresponding to the metropolitan area code and the city code. 
Check the following link for more about NUTS3 code:
https://it.wikipedia.org/wiki/Nomenclatura_delle_unit%C3%A0_territoriali_per_le_statistiche_dell%27Italia
While LAU2 can be easily found as "codice ISTAT" of the city of interest.
You are asked to put the LAU2 as a string consisting of 6 digits. In case of missing digits then, put zeros from the left to reach a string consisting of 6 digits.
5) Choose the coordinate reference system;
6) Choose the coordinate reference system zone, to be expressed as integer, according to the UTM fuso to reproject polygons and following the minimum projected bounds coordinates expressed as a list as follows:
[min_x, min_y, min_z] respectively associated with east, north and height;
7) Specify what are the target of your interest(e.g. building) to properly filter open street map data;
8) Specify the target of building of your interest (e.g. residential) for later building use assignation.
It is strongly suggested to use this application for one target a time and merge at the end different output datasets.
If simultaneous different building targets data managing is needed, the code require some adaptation to cope it.
9) Give as a list the fields you need for your application. 
Geometry, height, age, use destination, number of floors, area, gross floor area, building type, no. of families, no. of people per building, building census section number, 
tabula building type identifier, POD UID (randomly generated if not available), building infiltration rate (random generated in range [0,1] if not available), 
cooling system (boolean value randomly generated if not available), heating system (boolean value randomly generated too if not available), total energy demand, 
electricity energy demand, cooling energy demand and heating energy demand must be respectively the 
1st, the 2nd, the 3rd, the 4th, the 5th, the 6th, the 7th, the 8th, the 9th, the 10th, the 11th, the 12th, the 13th, the 14th, the 15th, the 16th, 17th, the 18th, the 19th and the 20th element of the list. 
In such way, the application is allowed to correctly work by retrieving them by exploiting list indices instead of headers name.
Additional features would require additional modules and then code adaptation;
10) Specify the input files path; 
11) Give as a list the fields of your interest after having read the metadata file, to properly filter the csv containing detailed data about buildings inside that area. 
12) Give as a list of strings the names of the columns where each census section unique identifier is stored respectively in the provided csv and shapefile, to filter data inside the previously selected bounding box. 

Pay attention, please, to the fact that only Point, Polygon and MultiPolygon geometries are managable. 
Objects with different geometries would require code adaptation in the module methods\consistency_checking.py.

Census section data can be retrieved at the following link:
https://www.istat.it/it/archivio/104317

A virtual environment creation is strongly suggested. The needed packages are:

chardet
geopy
geopandas
openpyxl
osmnx
pandapower
pandas
pyproj
requests
rtree
scipy
shapely