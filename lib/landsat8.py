class LicenseError(Exception):
    pass

class SpatialRefProjError (Exception):
    pass

import arcpy as ap
import numpy as np
import os, sys, time, glob, math, string

##  Function to process a landsat scene directory
##
##  @output : Reprojected bands, TOA Reflectance, Calculated NDVI and EVI
def process_landsat(path, output=None):
    '''Calc/converts TOA Reflectance for each band in the directory

        @type path:     c{str}
        @param path:    Path to raw landsat directory
        @rtype output:  c{str}
        @return output: Makes directry with processed bands
    '''

    ap.env.workspace = path
    print "Workspace Environment set to " + str(path)

    
    if output is None:
        output = os.path.join(path, "processed")
        if os.path.exists(output):
            sys.exit(0)
            print "\nDirectory for reprojection already Exisits"
        else:
            os.mkdir(output)
            print "\nCreated the output directory: " + output
    else:
        if os.path.exists(output):
            sys.exit(0)
            print "\nDirectory for reprojection already Exisits"
        else:
            os.mkdir(output)
            print "\nCreated the output directory: " + output

    mtl = parse_mtl(path)
    
    try:
        ## Create directory in Processed out put for the TOA Reflectance
        toa = os.path.join(output, 'toa')
        
        reproject(path, output, mtl)
        calc_toa(output, toa, mtl)
        stack_bands(toa, mtl)
        calc_ndvi(toa, mtl)
        ##pan_sharpen(output, mtl)

    finally:
        print "\n Completed processing landsat data for scene " + str(mtl['L1_METADATA_FILE']['LANDSAT_SCENE_ID'])


def reproject(input_dir, output_dir, meta):
    ''' Reproject raster band

        @param   input_dir: landsat 8 directory after unzip
        @type    input_dir: c{str}
        @param   meta: metadata parsed from MTL file
        @type    meta: dictionary
        @return  output_dir: output directory path
    '''

##    ##  Setting output directory id not defined
##
##    if output_dir is None:
##        output_dir = os.path.join(input_dir, "processed")
##        if os.path.exists(output_dir):
##            sys.exit(0)
##            print "\nDirectory for reprojection already Exisits"
##        else:
##            os.mkdir(output_dir)
##            print "\nCreated the output directory: " + output_dir
##    else:
##        if os.path.exists(output_dir):
##            sys.exit(0)
##            print "\nDirectory for reprojection already Exisits"
##        else:
##            os.mkdir(output_dir)
##            print "\nCreated the output directory: " + output_dir

    
    ap.env.workspace = input_dir

    rasters = ap.ListRasters('*.TIF')
    ms_bands = [band for band in rasters if (band_nmbr(band) != None)]
    bqa_band = [band for band in rasters if (band_nmbr(band) == None)][0]

    try:
        checkout_Ext("Spatial")
        print "\nReprojecting and Cleaning landsat bands."
        for band in ms_bands:
            print "\nReclassifying NoData for band " + band
            outCon = ap.sa.Con(ap.sa.Raster(bqa_band) != 1, ap.sa.Raster(band))
            out_band = os.path.join(output_dir, band)

            print "Reprojecting band to NAD 83 - UTM Zone 12N"
            ap.ProjectRaster_management(outCon, out_band, "PROJCS['NAD_1983_UTM_Zone_12N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-111.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]", "NEAREST", "30", "WGS_1984_(ITRF00)_To_NAD_1983", "", "PROJCS['WGS_84_UTM_zone_12N',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['false_easting',500000.0],PARAMETER['false_northing',0.0],PARAMETER['central_meridian',-111.0],PARAMETER['scale_factor',0.9996],PARAMETER['latitude_of_origin',0.0],UNIT['Meter',1.0]]")

    except SpatialRefProjError:
        ap.AddError ("Spatial Data must use a projected coordinate system to run")

    except LicenseError:
        ap.AddError ("Spatial Analyst license is unavailable")

    finally:
        checkin_Ext("Spatial")


def calc_toa(input_dir, output_dir, meta):
    '''Raster Algebra to run reflectance equation

        @param   input_dir: landsat 8 directory after unzip
        @type    input_dir: c{str}
        @param   meta: metadata parsed from MTL file
        @type    meta: dictionary
        @return  output: out raster path
    '''

    ##  Setting output directory id not defined
    ap.env.workspace = input_dir

    if output_dir is None:
        output_dir = os.path.join(input_dir, "TOA")
        if os.path.exists(output_dir):
            sys.exit(0)
            print "\nDirectory for reprojection already Exisits"
        else:
            os.mkdir(output_dir)
            print "\nCreated the output directory: " + output_dir
    else:
        if os.path.exists(output_dir):
            sys.exit(0)
            print "\nDirectory for reprojection already Exisits"
        else:
            os.mkdir(output_dir)
            print "\nCreated the output directory: " + output_dir

    rasters = ap.ListRasters('*.TIF')
    ms_bands = [band for band in rasters if (band_nmbr(band) != None)]

    try:

        checkout_Ext("Spatial")

        print "\nCalculating TOA Reflectance for landsat 8 bands"
        for band in ms_bands:

            print "\nBegining to calculate TOA for " + band
            number = band_nmbr(band)
            raster_band = ap.sa.Raster(band)
            out_band = str(meta['L1_METADATA_FILE']['LANDSAT_SCENE_ID']) + 'TOA_B' + str(number) + '.img'
        
            sun_elev = float(meta['IMAGE_ATTRIBUTES']['SUN_ELEVATION'])
            rad_mult = float(meta['RADIOMETRIC_RESCALING']['RADIANCE_MULT_BAND_' + str(number)])
            rad_add = float(meta['RADIOMETRIC_RESCALING']['RADIANCE_ADD_BAND_' + str(number)])
        
            toa_refl = (rad_mult*raster_band + rad_add)/(math.sin(sun_elev))

            print "Writing " + str(out_band)
            toa_refl.save(os.path.join(output_dir, out_band))

    except SpatialRefProjError:
        ap.AddError ("Spatial Data must use a projected coordinate system to run")

    except LicenseError:
        ap.AddError ("Spatial Analyst license is unavailable") 	

    finally:
        checkin_Ext("Spatial")


def stack_bands(path, meta):
    '''Stack Landsat bands 1 - 11 within a directory

        @param output: path of output reflectance.
        @ptype output: c{str}
    '''

    print "\nStacking bands to create a composite raster"

    ap.env.workspace = path
    rasters = ap.ListRasters()
    rgb_rasters = [rgb for rgb in rasters if band_nmbr(rgb) >= 2 and band_nmbr(rgb) <= 5]
    out_stack = str(meta['L1_METADATA_FILE']['LANDSAT_SCENE_ID']) + 'STACK_RGB.img'
    print "\nRGB Bands:"
    print " " + str(rgb_rasters)

    ap.CompositeBands_management(rgb_rasters, out_stack)    
    print "\nComposite Stack Complete!"


def calc_ndvi(path, meta):
    '''Use the pan chromatic layer to pan-sharen the Blue, Green, Red, & NIR stack

        @param   path:  Directory containing @param stack
        @ptype   path:  c{str}
        @param   meta:  Metadat built from MTL.txt
        @ptype   meta:  Dictionary of landsat scene metadata
        @return  Output composite image with pan-sharpening
    '''

    ap.env.workspace = path
    output = str(meta['L1_METADATA_FILE']['LANDSAT_SCENE_ID']) + '_NDVI.img'
    red = ap.sa.Raster(ap.ListRasters('*B4.img')[0])
    nir = ap.sa.Raster(ap.ListRasters('*B5.img')[0])

    try:
        checkout_Ext("Spatial")
        
        print "\nCalculating NDVI"
        ndvi = (nir-red)/(nir+red)

        print "\nSaving NDVI As: " + str(output)
        ndvi.save(output)

        print "\nFinished NDVI"

    except SpatialRefProjError:
        ap.AddError ("Spatial Data must use a projected coordinate system to run")

    except LicenseError:
        ap.AddError ("Spatial Analyst license is unavailable") 	

    finally:
        checkin_Ext("Spatial")
        
        # arcpy.Delete_management("forGettingLoc")


## Funtion not built into function "process_landsat"
def pan_sharpen(path, meta):
    '''Use the pan chromatic layer to pan-sharen the Blue, Green, Red, & NIR stack

        @param   stack: Input composite image stack
        @ptype   stack: c{string}
        @param   meta:  Metadat built from MTL.txt
        @ptype   meta:  Dictionary of landsat scene metadata
        @return  Output composite image with pan-sharpening
    '''
    ap.env.workspace = path
    out_stack = str(meta['L1_METADATA_FILE']['LANDSAT_SCENE_ID']) + 'STACK_PANSHARP.img'

    rasters = ap.ListRasters()
    rgb = [img for img in rasters if 'STACK_BGRNIR' in img]
    pan = [img for img in rasters if 'B8.img' in img]

    print rgb
    print pan
    print ""
    print "Begining Pan Sharpen"
    ap.CreatePansharpenedRasterDataset_management(rgb[0], "3", "2", "1", "4", out_stack, pan[0], "Brovey") 

    print ""
    print "Pan Sharpen Complete"


##
##  Helper FUnctions
##  
def band_nmbr(filename):
    ''' Find the landsat band number

        @param   filename: Input landsat band to extract band number
        @ptype   filename: c{str}
        @return  Band number
        @rtype   c{int}
    '''
    try:
        band_num = int(filename.split('_')[1].split('.')[0].replace('B', ''))
        return band_num
    except:
        pass
    

##  Verify and create directory
def check_Dir(input_path, named_path):
    if input_path is None:
        input_path = os.path.join(input_path, named_path)
        if os.path.exists(input_path):
            sys.exit(0)
            print "\nDirectory for reprojection already Exisits"
        else:
            os.mkdir(input_path)
            print "\nCreated the output directory: " + input_path
    else:
        if os.path.exists(input_path):
            sys.exit(0)
            print "\nDirectory for reprojection already Exisits"
        else:
            os.mkdir(input_path)
            print "\nCreated the output directory: " + input_path

    
##  Checkout ArcGIS extension by name
def checkout_Ext(ext_type):
    if ap.CheckExtension(ext_type) == 'Available':
        ap.CheckOutExtension(ext_type)
        print "\nChecking out " + ext_type + " Extension"
    else:
        raise LicenseError
        print "\nCannot checkout " + ext_type + " Extension"


##  Checkin ArcGIS extension by name
def checkin_Ext(ext_type):
    ap.CheckInExtension(ext_type)
    print "\nChecking in " + ext_type + " Extension"
    
##  'parse_mtl' Function Thanks To:
##      Copyright (c) 2011 Australian Government, Department of Sustainability, Environment, Water, Population and Communities
##      https://code.google.com/p/metageta/source/browse/trunk/lib/formats/landsat_mtl.py?r=608    
def parse_mtl(path=None):
    '''Traverse the downloaded landsat directory and read MTL file

        @type    path: c{str}
        @param   path: Path to landsat file directory
        @rtype   C{dict}
        @return  Dictionary
    '''

    if path is None:
        path = "c:/landsat"

    
    files = os.listdir(path)
    mtl = [txt for txt in files if '.txt' in txt][0]
    lines = iter(open(os.path.join(path, mtl)).readlines())
    hdrdata= {}

    line = lines.next()

    while line:
        line=[item.strip() for item in line.replace('"','').split('=')]
        group=line[0].upper()
        if group in ['END;','END']:break
        value=line[1]
        if group in ['END_GROUP']:pass
        elif group in ['GROUP']:
            group=value
            subdata={}
            while line:
                line=lines.next()
                line = [l.replace('"','').strip() for l in line.split('=')]
                subgroup=line[0]
                subvalue=line[1]
                if subgroup == 'END_GROUP':
                    break
                elif line[1] == '(':
                    while line:
                        line=lines.next()
                        line = line.replace('"','').strip()
                        subvalue+=line
                        if line[-1:]==';':
                            subvalue=eval(subvalue.strip(';'))
                            break
                else:subvalue=subvalue.strip(';')
                subdata[subgroup]=subvalue
            hdrdata[group]=subdata
        else: hdrdata[group]=value.strip(');')
        line=lines.next()
    return hdrdata

def pretty(d, indent=0):
   for key, value in d.iteritems():
      print '\t' * indent + str(key)
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print '\t' * (indent+1) + str(value)


##  Run Process

process_landsat("c:/landsat")


