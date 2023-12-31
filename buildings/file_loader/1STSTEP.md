Welcome

Here are listed the first steps to be followed to use this application correctly.
The configuration must be done appropriately only by setting the value of fields in the file config/config.json:

1) First, you must specify the address around which you want to build your bounding box in the following format:
   - address, CAP, City XX, Country ;
2) You also have to specify the size of the bounding box by expressing the distance (in meters) from the previously specified address and the desired resolution for elevation data mapping after the bounding box has been split in a grid.
Please adequately set the resolution since the elevation is obtained through HTTP get request to open elevation API, which supports at most 512 locations per request.
Then the resolution according to which the bounding box is discretized must be chosen in order not to exceed this number;
3) Also, the city of interest must be appropriately specified filling the fields "provincia", "comune", "nation" and "h_slm" with the corresponding city height value (with the sea level as reference) as integer;
4) Following, the fields "NUTS3" and "LAU2" must be filled respectively with strings corresponding to the metropolitan area code and the city code. 
Check the following link for more about NUTS3 code:
https://it.wikipedia.org/wiki/Nomenclatura_delle_unit%C3%A0_territoriali_per_le_statistiche_dell%27Italia
While LAU2 can be easily found as "codice ISTAT" of the city of interest.
You are asked to put the LAU2 as a string of 6 digits. In case of missing digits, then, put zeros from the left to reach a string consisting of 6 digits;
5) Choose the coordinate reference system;
6) Choose the coordinate reference system zone, to be expressed as integer, according to the UTM fuso to reproject polygons and following the minimum projected bounds coordinates expressed as a list as follows:
[min_x, min_y, min_z] respectively associated with east, north and height;
7) Specify what are the target of your interest (e.g. building) to properly filter open street map data;
8) Specify the target of the building of your interest (e.g. residential) for later building use assignment.
It is strongly suggested to use this application for one target at a time and merge in the end different output datasets.
If simultaneous different building targets data management is needed, the code requires some adaptation to cope with it;
9) Give as a list the fields you need for your application. 
Geometry, height, age, use destination, number of floors, area, gross floor area, building type, no. of families, no. of people per building, building census section number, 
tabula building type identifier, POD UID (randomly generated if not available), building infiltration rate (randomly generated in a later specified range if not available), 
cooling system (boolean value randomly generated if not available), heating system (boolean value randomly generated too if not available), total energy demand, 
electricity energy demand, cooling energy demand and heating energy demand must be, respectively the 
1st, the 2nd, the 3rd, the 4th, the 5th, the 6th, the 7th, the 8th, the 9th, the 10th, the 11th, the 12th, the 13th, the 14th, the 15th, the 16th, 17th, the 18th, the 19th and the 20th element of the list. 
In such a way, the application can correctly work by retrieving them by exploiting list indices instead of headers' names.
Additional features would require additional modules and then code adaptation;
10) Specify the input files path; 
11) Give as a list the fields of your interest after having read the metadata file to properly filter the csv containing detailed data about buildings inside that area;
12) Give as a list of strings the names of the columns where each census section's unique identifier is stored in the provided csv and shapefile to filter data inside the previously selected bounding box. 

Pay attention, please, to the fact that only Point, Polygon, and MultiPolygon geometries are manageable. 
Objects with different geometries would require code adaptation in the module methods\consistency_checking.py.

Census sections data can be retrieved at the following link:
https://www.istat.it/it/archivio/104317.