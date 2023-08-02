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

The user is also required to put the acquisition method through which energy consumption data have been achieved and the interpolation method both as a string, 
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

Eventually, the energy measurement period must be specified by putting the start date and the end date in the date format "YYYY-MM-DD".

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
That script outputs a csv file containing a daily record for a year referred to the chosen weather element.

First, the user must configure the parameters for correctly setting the weather object inside the output cityjson.
Then, user is required to put the weather element as a string by strictly choosing one among the following weather elements:
  
  "airTemperature";
  "humidity";
  "windSpeed";
  "cloudiness";
  "globalSolarIrradiance";
  "directSolarIrradiance";
  "diffuseSolarIrradiance";
  "terrestrialEmission";
  "downwardTerrestrialRadiation";
  "daylightIlluminance".

Following, the measured weather element as a string (e.g. temperature, humidity...), the acquisition method through which weather data have been achieved and the interpolation method both as a string
as for energy data, strictly choosing one among the methods and interpolation strategies previously listed.

Thus, the weather measurement period must be specified by putting the start date and the end date in the date format "YYYY-MM-DD".

After having correctly set the parameters for the weather city object, the user is required to set the average value associated with each month and the standard deviation both as float or integer values.
Those values will be the parameters of the gaussian distributions exploited for generating sample weather data.

In the same file, also the path for retrieving weather data and the unit of measurement of them must be specified both as a string.
Those two, are required even if weather data are still available with no need of generating "fake" samples.

Pay attention to the fact that the code has been developed to deal with same-structured weather data as before  (csv with just one column) and for managing ONE weather file a time, independently on the kind of data.
In case of different or several input weather data, code adaptations might be needed.