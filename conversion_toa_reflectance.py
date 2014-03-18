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
    
    def filter_toa():
        ret_bands = []
        all_bands = [band for band in os.listdir(path) if '.TIF' in band]

        for band in all_bands:
            band_nums = ['B2.', 'B3.', 'B4.', 'B5.', 'B6.','B7.', 'B8.']
            for num in band_nums:
                if num in band:
                    ret_bands.append(band)

        return ret_bands
        
        
    all_bands = [band for band in os.listdir(path) if '.TIF' in band]
    toa_bands = filter_toa()
    mtl = parse_mtl(path)
    
    if output is None:
        output = os.path.join(path, 'processed_toa')
        if os.path.exists(output):
            print "Directory already Exisits"
        else:
            os.mkdir(output)
            print "Created the output directory: " + output
    else:
        if os.path.exists(output):
            sys.exit("Directory already exists. Please rename the directory: " + output)
        else:
            os.mkdir(output)
            print "Created the output directory: " + output

    try:
        if ap.CheckExtension('Spatial') == 'Available':
            ap.CheckOutExtension('Spatial')
        else:
            raise LicenseError
        
        for band in toa_bands:
            calc_toa(band, output, mtl)

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
        @typr    meta: dictionary
        @return  output: out raster path
    
    '''
    band = band_nmbr(band_file)
    raster_band = ap.sa.Raster(band_file)
    out_band = 'toa_refl_band_' + str(band) + '.img'
    
    sun_elev = float(meta['IMAGE_ATTRIBUTES']['SUN_ELEVATION'])
    rad_mult = float(meta['RADIOMETRIC_RESCALING']['RADIANCE_MULT_BAND_' + str(band)])
    rad_add = float(meta['RADIOMETRIC_RESCALING']['RADIANCE_ADD_BAND_' + str(band)])
    
    print ""
    print "Calculating TOA Reflectance for Band " + str(band)
    toa_refl = (rad_mult*raster_band + rad_add)/(math.sin(sun_elev))

    print "Writing " + str(out_band)
    toa_refl.save(os.path.join(output, out_band))

    
def band_nmbr(filename):
    band_number = filename.split('_')[1].split('.')[0].replace('B', '')
    return band_number
    
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

process_toa('c:/landsat')
