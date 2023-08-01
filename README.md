At this stage, building data can be easily retrieved at the following path:

"buildings\cityname_buildingtarget"

e.g. "buildings\processing\Torino_residential"

Thus, the GeoDataframe containing all relevant information about target buildings is now available for conversion in CityJSON. 
The user is required to specify in the config/cityjson_config.json, the required application extension domains names as a list of dictionaries each one built as it follows:

{
  "ADE_name_for_single_objects": {
    "name": "ADE_name_for_CityModel_extensions",
    "version": ADE_version, (as float)
    "url": "https://sampleurl.com/schemas/extensions/file.ext.json"
  }
}
The extension file, if retrieved from a github public repository, requires to put as url the one for reaching the raw file.

Also, the required level of detail according to the specifications in https://3d.bk.tudelft.nl/lod/ must be put as a string, 
and the link for the output crs which must be compliant to the following sample link used for UTM zone 32 crs:
https://www.opengis.net/def/crs/EPSG/0/32632

Eventually, the acquisition method through which energy consumption data have been achieved and the interpolation method must be put both as a string, 
strictly choosing one among the following methods and interpolation strategies respectively:

  "measurement";
  "simulation";
  "calibratedSimulation";
  "estimation";
  "unknown".

  "averageInPrecedingInterval";
  "averageInSucceedingInterval";
  "constantInPrecedingInterval";
  "constantInSucceedingInterval";
  "continuous";
  "discontinuous";
  "instantaneousTotal";
  "maximumInPrecedingInterval";
  "maximumInSucceedingInterval";
  "minimumInPrecedingInterval";
  "minimumInSucceedingInterval";
  "precedingTotal";
  "succeedingTotal".

The code has been written for conversion to CityJSON v. 1.1. 
If to a later or an older version conversion is needed, the code would require some adaptations in the module methods/cj_converter.py.

Pay also attention, please, to the fact that only Point, Polygon and MultiPolygon geometries are managable. 
Objects with different geometries would require code adaptation even in this case in the module methods\cj_converter.py.

Building height coordinates have been instead obtained under the assumption of constant terrain elevation. 
For sloped city, it is, then, strongly suggested to integrate additional modules for precise elevation calculation. 

Additional modules for further ADEs must be added into the folder methods/ade. 
Additional ADEs modules would require to be imported into the script to_cj.py.

In the same folder, another configuration file is there. 
It is needed for running the "weather_data_generator.py" script, in case of not available weather data.
That script outputs a csv file containing a daily record for a year ONLY referred to air temperature.
The user is required to put the average temperature associated with each month and the standard deviation both as float or integer values, expressed in degrees.
Those values will be the parameters of the gaussian distributions exploited for generating sample temperature data.

In the same file, also the path for retrieving weather data must be specified. 

Pay attention to the fact that the code has been developed to deal with same-structured weather data as before, independently on the kind of data (csv with just one column).
In case of different input weather data, some code adaptations might be needed.