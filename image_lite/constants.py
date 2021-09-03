from django.utils.functional import cached_property


'''
Map of allowed file extensions -> format key
Lower case entries, and variations in spelling 
e.g. 'jpg'/'jpeg'
'''    
# This needs to be a union of the filehandling of the possible 
# libraries, largely Pillow Wand, OpenCV
# Pillow
#   django.core.validators.get_available_image_extensions
# Imagemagic
#   > identify -list format
# (no Wand implementation?)
# I think we assume if Pillow can, Wand can. Also, we stay conservative.
# Pillow extensions: bmp, dib, gif, tif, tiff, 
# jfif, jpe, jpg, jpeg, pbm, pgm, ppm, pnm, png, apng, blp, bufr, cur, 
# pcx, dcx, dds, ps, eps, fit, fits, fli, flc, ftc, ftu, gbr, grib, h5, 
# hdf, jp2, j2k, jpc, jpf, jpx, j2c, icns, ico, im, iim, mpg, mpeg, 
# mpo, msp, palm, pcd, pdf, pxr, psd, bw, rgb, rgba, sgi, ras, tga, icb,
# vda, vst, webp, wmf, emf, xbm, xpm.
# Map possible (lowercase) file extensions -> internal format
# Avoid cross-media such as pdf, ps, mpg, even if libraries can handle.
EXTENSION_TO_APP_FORMAT = {
    'bmp' : 'bmp',
    'jpg' : 'jpg',
    'jpeg' : 'jpg',
    'png' : 'png',
    'gif' : 'gif',
    'ico' : 'ico',
    'rgb' : 'rgb',
    'rgba' : 'rgb',
    'tiff': 'tiff',
    'tif': 'tiff',
    'webp' : 'webp',
    'xbm' : 'xbm',
    'xpm' : 'xpm',
}

'''
Formats accepted.
This list is used throughout the app, and is definitive. The entries can
be used for new file extensions. However, for verification and other 
code, other collections in this module are preferred. The main use in 
code is for displaying nice messages for the user. 
'''
## To get extensions from internal format, use the internal format 
# string!
IMAGE_FORMATS = set()
for v in EXTENSION_TO_APP_FORMAT.values():
     IMAGE_FORMATS.add(v)

# def extensions_maxlen():
    # '''
    # max length of listed extensions, including the period.
    # eg '.tiff' returns 5
    # '''
    # m = 0
    # for f in IMAGE_FORMATS:
        # l = len(f)
        # if (l > m):
            # m = l
    # # for the period i.e '.png' is 4
    # m += 1
    # return m


'''
Map of uppercase format keys -> app formats.
This map will work for Pillow and Wand libraries.
'''
# Order matters. Put the reverse conversion last so it overwrites on 
# reverse generation
FORMAT_UCLIB_TO_APP = {
    'BMP' : 'bmp',
    'GIF' : 'gif',
    'ICO' : 'ico',
    'MPO' : 'jpg',
    'JPG' : 'jpg',
    'JPEG' : 'jpg',
    'PNG32' : 'png',
    'PNG64' : 'png',
    'PNG' : 'png',
    'RGB' : 'rgb',
    'RGBA' : 'rgb',
    'TIFF64' : 'tiff',
    'TIFF' : 'tiff',
    'WEBP' : 'webp',
}

'''
Map of app formats -> uppercase format keys.
This map will work for Pillow and Wand libraries.
'''
FORMAT_APP_TO_UCLIB = {}
for k,v in FORMAT_UCLIB_TO_APP.items():
    FORMAT_APP_TO_UCLIB[v] = k
    
