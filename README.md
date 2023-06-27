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

Also, the required level of detail according to the specifications in https://3d.bk.tudelft.nl/lod/ must be put as a string, and the link for the output crs which must be compliant to the following sample link used for UTM zone 32 crs:
https://www.opengis.net/def/crs/EPSG/0/32632

The code has been written for conversion to CityJSON v. 1.1. 
If to a later or an older version conversion is needed, the code would require some adaptations in the module methods/cj_converter.py.

Pay also attention, please, to the fact that only Point, Polygon and MultiPolygon geometries are managable. 
Objects with different geometries would require code adaptation even in this case in the module methods\cj_converter.py.

Building height coordinates have been instead obtained under the assumption of constant terrain elevation. 
For sloped city, it is, then, strongly suggested to integrate additional modules for precise elevation calculation. 

Additional modules for further ADEs must be added into the folder methods/ade. 
Additional ADEs modules would require to be imported into the script to_cj.py.