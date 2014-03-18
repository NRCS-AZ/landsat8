
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
            band_nums = ['B2.', 'B3.', 'B4.', 'B5.', 'B6.','B7.', 'B8.', 'B9.']
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
            sys.exit("Directory already exists. Please rename the directory: " + output)
        else:
            os.mkdir(output)
            print "Created the output directory: " + output
    else:
        if os.path.exists(output):
            sys.exit("Directory already exists. Please rename the directory: " + output)
        else:
            os.mkdir(output)
            print "Created the output directory: " + output

    print toa_bands

def calc_toa(band, out_band, meta):
    '''Raster Algebra to run reflectance equation

        @param   band:image TIF of landsat 8 band
        @type    band: GEOTIfF file
        @param   meta: metadata parsed from MTL file
        @typr    meta: dictionary
        @return  out_band: out raster of band
    
    '''
    
    
    
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
