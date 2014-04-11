#Landsat 8 Processing with ESRI Arcpy Lib#
**Version: 0.0.1**<br>
**Dependencies: ArcGIS > = 10.0**

A library to prepare and process Landsat 8 data

- Reproject Landsat scenes
- Process Landsat bands based on sensor reflectance
- Create composite images from layer band stacks
- Create common raster indices i.e. NDVI, EVI, SAVI...

<br>
##Install##
Download and unzip the repository

![Imgur](http://i.imgur.com/VmyORTH.png?1)

- Open an ArcMap project
- Open ArcToolbox
- Right Click on the ArcToolbox icon and select Add Toolbox
- Navigate to the unzipped folder and select the file "landsat_8.tbx" and click Open
- Landsat 8 Toolbox is now ready for use

<br>
##Downloading Landsat 8 Scenes##
Go to the USGS Landsat Look website at [landsatlook.usgs.gov](http://landsatlook.usgs.gov/) zoom to the desired AOI.  Use the advance query functionality to choose a desired satellite and time range.  For Landsat 8 data, the satellite sensor will be "OLI"

Once the AOI, OLI, and date range are selected and have been applied, click the "metadata" button to view each individual scene and click "add to cart" to later download the data.  Once all of the desired Landsat 8 scenes have been added to the cart, you can download the data by clicking "view cart".

Select the "Level 1" data (aprox. file size: 500mb - 1000mb) to download for processing.

<br>
##Using the Toolbox##
####Input####
- Open the Landsat_8 toolbox and select the "Bulk Scene Processing"
-  Select the folder containing the downloaded scene containing the .TIF and .MTL files
 **[NOTE: Keep only one downloaded scene of TIFFs and MTL per folder]**
- Select the desired coordinate system to convert the scenes
 **[DEFAULT Coords: WGS 84]**
- Click "OK" to run

####Output####
- A folder is created inside the Landsat scene folder
- Each TIF is re-projected into the selected coordinate system and the assigned proper "NoData" values
- The "toa" folder processes the re-projected scenes by re-calculating the pixel numbers by applying the reflectance value.
- Also, NDVI for vegetation and a False Color composite for greenness is created.


<br>
##ToDo##
- Add additional algorithms to bulk process
  - SATV
  - EVI
  - Soil Types
  - etc.
- Add new scripts to the toolbox to break down the bulk processing into different functions
- Add support for legacy Landsat Satellite Sensors

<br>
##Resources##
[Landsat Look](http://landsatlook.usgs.gov/): Landsat 8 Data Download

[Landsat 8 Imagery Processing](https://landsat.usgs.gov/Landsat8_Using_Product.php): Equations for Raster DN Conversion

[Parsing Scene MetaData](https://code.google.com/p/metageta/source/browse/trunk/lib/formats/landsat_mtl.py?r=608): Landsat Scene **_MTL.txt_** Metadata parsing function thanks to:

- _Copyright (c) 2011 Australian Government, Department of Sustainability, Environment, Water, Population and Communities_

<br>
##Contact##

####Andrew Burnes####

Arizona NRCS

apburnes@gmail.com

