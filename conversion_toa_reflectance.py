class LicenseError(Exception):
    pass

class SpatialRefProjError (Exception):
    pass

import arcpy as ap
import numpy as np
import os, sys, time, glob, math, string


def process_toa(path, output=None):
    '''Calc/converts TOA Reflectance for each band in the directory

        @type path:     c{str}
        @param path:    Path to raw landsat directory
        @rtype output:  c{str}
        @return output: Makes directry with processed bands
    '''

    ap.env.workspace = path
    print "Workspace Environment set to " + str(path)
    print ""

    all_bands = [band for band in os.listdir(path) if '.TIF' in band and not '_BQA.TIF' in band]
    mtl = parse_mtl(path)
    
    if output is None:
        output = os.path.join(path, 'processed_toa')
        if os.path.exists(output):
            sys.exit(1)
            print ""
            print "Directory already Exisits"
        else:
            os.mkdir(output)
            print ""
            print "Created the output directory: " + output
    else:
        if os.path.exists(output):
            sys.exit(1)
            print ""
            print "Directory already Exisits"
        else:
            os.mkdir(output)
            print ""
            print "Created the output directory: " + output

    try:
        if ap.CheckExtension('Spatial') == 'Available':
            ap.CheckOutExtension('Spatial')
            print ""
            print "Checking out Spatial Analytst Extension"
        else:
            raise LicenseError
            print ""
            print "Cannot checkout Spatial Analyst Extension"
        
        for band in all_bands:
            calc_toa(band, output, mtl)

        print ""
        print "Finished TOA Reflectance Conversion"

        stack_bands(output, mtl)
        ##pan_sharpen(output, mtl)

    except SpatialRefProjError:
        ap.AddError ("Spatial Data must use a projected coordinate system to run")

    except LicenseError:
        ap.AddError ("Spatial Analyst license is unavailable") 	

    finally:
        ap.CheckInExtension("Spatial")
        # arcpy.Delete_management("forGettingLoc")


def calc_toa(band_file, output, meta):
    '''Raster Algebra to run reflectance equation

        @param   band_file:image TIF of landsat 8 band
        @type    band_file: GEOTIfF file
        @param   meta: metadata parsed from MTL file
        @type    meta: dictionary
        @return  output: out raster path
    
    '''
    band = band_nmbr(band_file)
    raster_band = ap.sa.Raster(band_file)
    out_band = str(meta['L1_METADATA_FILE']['LANDSAT_SCENE_ID']) + 'TOA_B' + str(band) + '.img'
    
    sun_elev = float(meta['IMAGE_ATTRIBUTES']['SUN_ELEVATION'])
    rad_mult = float(meta['RADIOMETRIC_RESCALING']['RADIANCE_MULT_BAND_' + str(band)])
    rad_add = float(meta['RADIOMETRIC_RESCALING']['RADIANCE_ADD_BAND_' + str(band)])
    
    print ""
    print "Calculating TOA Reflectance for Band " + str(band)
    toa_refl = (rad_mult*raster_band + rad_add)/(math.sin(sun_elev))

    print "Writing " + str(out_band)
    toa_refl.save(os.path.join(output, out_band))

def stack_bands(path, meta):
    '''Stack Landsat bands 1 - 11 within a directory

        @param output: path of output reflectance.
        @ptype output: c{str}
    '''

    print ""
    print "Stacking bands to create a composite raster"

    ap.env.workspace = path
    rasters = ap.ListRasters()
    rgb_rasters = [rgb for rgb in rasters if band_nmbr(rgb) >= 2 and band_nmbr(rgb) <= 5]
    out_stack = str(meta['L1_METADATA_FILE']['LANDSAT_SCENE_ID']) + 'STACK_BGRNIR.img'
    print ""
    print "RGB Bands:"
    print rgb_rasters

    ap.CompositeBands_management(rgb_rasters, out_stack)    
    print ""
    print "Composite Stack Complete!"

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
        if ap.CheckExtension('Spatial') == 'Available':
            ap.CheckOutExtension('Spatial')
            print ""
            print "Checking out Spatial Analytst Extension"
        else:
            raise LicenseError
            print ""
            print "Cannot checkout Spatial Analyst Extension"
        
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
        ap.CheckInExtension("Spatial")
        # arcpy.Delete_management("forGettingLoc")

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
    
def band_nmbr(filename):
    try:
        band_num = int(filename.split('_')[1].split('.')[0].replace('B', ''))
        return band_num
    except:
        pass


## 'parse_mtl' Function Thanks To:
## Copyright (c) 2011 Australian Government, Department of Sustainability, Environment, Water, Population and Communities

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
path = "c:/landsat/processed_toa"
mtl = parse_mtl("c:/landsat")

calc_ndvi(path, mtl)


