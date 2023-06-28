For correct synthetic distribution grid generation, you need to change the virtual environment.
The new environment must be configured for all needed packages correct installation (in order to avoid conflicts with other installed libraries).

Needed environment configuration file is available on "envs_config" folder.

The user is also required to configure the needed parameters to allow for proper working the utility network generator.
In the file "config/ding0_config.json", the user must respectively put:
1) The number of the chosen MV_district from the db available at the following link:
    https://openenergy-platform.org/dataedit/view/grid/ego_dp_mv_griddistrict?view=268
    After having filtered data according to:
    - version --> v0.4.5
2) Once chosen the MV_district, the user is required to also put the geometry of the multipolygon the considered MV_district is built over, by copying and pasting the value corresponding to the field "geom".
It corresponds to a long exa-decimal string which represents a compressed form of the boundaries of the district. 