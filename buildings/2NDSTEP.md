Now you have all the files needed for building spatial analysis for further simulation purposes.
For this step, it is needed the knowledge of the files uploaded in the main and their relative fields to be taken into account.
First of all, you have to modify the file you find following the path file_loader/config/config.json: 

- The list associated with the key "building_filtering_values", by dropping the categories which are not relevant to your application.
Once done, the list must be replaced by a dict element containing the following keys and with each one associated a LIST containing different categories (even expressed as strings, PLEASE PAY ATTENTION IN AVOIDING TYPOS!!!) among the kept ones:
  - "not_specified" for very generic categories;
  - "AB" for apartment categories;
  - "SFH" for single family house categories;
  - "MFH" for multifamily house categories.
  - "TH" for terraced house categories;
Please notice that if no categories match the macro category expressed by the key, the list MUST be left empty.

Then, you also have to configure in the file config/processing_config.json:

1) The fields of the shapefile you want to keep as a list, but be careful! 
The building height header field must be placed as 1st element of the list while the building surface header must be placed as 3rd element.
In this way, you can retrieve them respectively as the elements with index 0 and 2 of the list.
This is a MANDATORY step to correctly configure the instance.
2) The building age columns of the census section csv file must be provided as a dictionary in which with each header of interest (key) is associated the corresponding age range as a value (info known after having first checked the metadata file); 
3) Same as point 3, the building number of floors columns and single floor assumed height;
4) Population columns name of the census section csv file as a list even in case of single values. 
The total number of families column's name must be the 1st element of the list in order to be retrieved by using index 0.
Instead, the total number of people column's name must be the 2nd element of the list in order to be retrieved by using index 1.
If additional columns are chosen to be used for further processing purposes, the code requires to be adapted;
5) Z-score threshold values as a list according to which buildings will be filtered (to respectively drop buildings too short and with too small gross floor area);
6) Infiltration rate range as a list according to which a random value will be generated, by assuming a uniform probability distribution in that range;
7) Cooling system probability intended as the probability that according to the study case location, buildings are cooled or not.
That probability must be put as a list of TWO values, where:
   - the first one is the probability that a given building is cooled;
   - the second one is the probability that a given building is not cooled.
It is then mandatory that, since those two values represent the parameters of a probability distribution, they must be set such that their summation must be equal to 1;
8) Heating system probability in the same way as for cooling system probability;
9Estimated yearly energy demand per household expressed in kWh (electricity, cooling and heating).

Please notice that the database might consist of not reliable data since stochastic methods have been employed to cope with missing data.
No economic and social factors have been taken into account for achieving those estimates.
Pay also attention to the fact that only resident population data have been taken into account.

Instead, regarding energy demand data, for following processing purposes, those values have been kept as SINGLE VALUES. 
The user is then responsible for guaranteeing that those associated with each one with a different kind of energy demand, MUST BE AVERAGED 
over the specified time resolution to get a single value at most.

For data managing purposes, take into account that building no. of floors data are expressed as strings, to be first converted into float or int if needed. 

One more need configuration step, at this stage, consists in filling the fields in the file config/tabula_config.json after having read the .xlsm input file.
In this file, the user is asked to specify instructions for data retrieving from tabula dataset for further information integration at the building level.
The required info are:

1) Tabula file path (be careful, the input file must be a .xlsm);
2) Sheet of interest name (Please notice that the code has been built for "Tab.Type.Building" sheet info retrieving, then for other sheets processing code adaptation might be needed);
3) Country code column name for filtering and country code (e.g. IT);
4) Distribution company code. This parameter is not actually concerned with tabula characterization but for further processing purposes, it must be placed here as a string. 
Usually, it is just a three-number code which identifies the company which provides energy distribution (e.g. IRETI --> "020")
5) Columns to be kept's name as a list. The code has been built for using the following fields, to be respectively put:
   1) "Code_BuildingType" as 1st element in order to be retrieved by using index 0;
   2) "Code_BuildingSizeClass" as 2nd element in order to be retrieved by using index 1;
   3) "Year1_Building" as 3rd element in order to be retrieved by using index 2;
   4) "Year2_Building" as 4th element in order to be retrieved by using index 3;

Please notice that additional features, if required, would make the code not totally suitable and then further modules integration or code adaptation might be required.