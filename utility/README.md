For correct synthetic distribution grid generation by ding0, you need to change the virtual environment.
The new environment must be configured for all needed packages correct installation (in order to avoid conflicts with other already installed libraries).

The needed environment configuration file is available on "envs_config" folder.

The user is also required to configure the needed parameters to allow for the proper working of the utility network generator.
In the file "config/ding0_config.json", the user must respectively put:
1) The number of the chosen MV_district from the db is available at the following link:
    https://openenergy-platform.org/dataedit/view/grid/ego_dp_mv_griddistrict?view=268
    After having filtered data according to the:
    - version --> v0.4.5
    
    For that purpose, the code has been written for loading ONE MV NETWORK AT ONCE. 
    If multiple network loading is required, the user is asked to modify the code for mapping the network to the output CityJSON to be compliant with the output of multiple network loading.
2) Once chosen the MV_district, the user is required to also put the geometry of the MultiPolygon the considered MV_district is built over, by copying and pasting the value corresponding to the field "geom".
It corresponds to a long exa-decimal string which represents a compressed form of the boundaries of the district. 

Instead, if needed data for utility network mapping are already available, ignore the steps listed below.