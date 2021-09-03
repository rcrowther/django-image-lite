from PIL import Image as PILImage
from io import BytesIO
from image_lite.filters import (
    Filter,
    FormatMixin,
    ResizeCropMixin,
    ResizeCropSmartMixin,
)
from image_lite import image_ops_pillow
from image_lite.constants import FORMAT_APP_TO_UCLIB, FORMAT_UCLIB_TO_APP



class PillowProcess:
            
    def process(self, src_file, model_args):
        src_image = PILImage.open(src_file)
        
        # write_attrs currently {format, jpeg_quality}
        # write_attrs = reform_save_info(
                    # self,
                    # FORMAT_UCLIB_TO_APP[src_image.format],
                    # model_args,
                    # )

        # stash the internal app format
        app_format = self.format
                            
        write_attrs = {'format': app_format}
        if app_format == 'jpg':
            write_attrs['jpeg_quality'] = self.jpeg_quality

        # mods on the save data
        # convert the returned format to PIL
        write_attrs['format'] = FORMAT_APP_TO_UCLIB[write_attrs['format']]
        
        # Add some general write attributes. Pillow ignores the unusable.        
        write_attrs['progressive'] = True  
        write_attrs['optimize'] = True

        # break out processing, it's the only action that changes
        # across different filters
        pil_dst = self.modify(src_image) or src_image

        # PIL raises error if given RGBA for JPEG output
        # in that case, no transparency
        if ((pil_dst.mode in ('RGBA', 'LA')) and (app_format == 'jpg')):            
            # If expressed, respect background colour. May be backing
            # a genuine transparency, so path of least surprise.
            if (hasattr(self, 'fill_color')):
                fc = self.fill_color
            else:
                fc = 'white'
            bg = PILImage.new('RGB', pil_dst.size, fc)
            bg.paste(pil_dst, pil_dst.getchannel('A'))
            pil_dst = bg
        
        #! test. I think that's the name.
        if ('jpeg_quality' in write_attrs):            
            write_attrs['quality'] = write_attrs['jpeg_quality']
        out_buff = BytesIO()
        pil_dst.save(
            out_buff,
            **write_attrs
        )
        return (out_buff, app_format)

    def modify(self, lib_image):
        '''
        Modify the image.
        'process hadles the image load and save. 'process' calls this 
        method to transform the image. Basely this is the only method
        that needs to be changed, even for a filter that performs a 
        new kind of transformation (no need to change the load and save 
        in 'process).
        Enabled methods should usually call super() to enable inherited 
        code.
        
        @lib_image the class used by the library to wrap image data
        '''
        # simple return. PIL uses returns
        return lib_image
        
    
        
class Format(FormatMixin, PillowProcess, Filter):
    '''Establish the format for an image. 
    Set iformat=None means the image is unchanged.
    '''
    
    
    
class Resize(ResizeCropMixin, Format):
    '''Resize n image.
    Shrinks inside the box defined by the given args. So the result will
    usually be smaller width or height than the given box.
    A base class e.g.
        class Large(image.Resize):
            width=513
            height=760    
            iformat='png'
    '''
    def modify(self, lib_image):
        i = image_ops_pillow.resize_aspect(
            lib_image, 
            self.width,
            self.height
        )
        return super().modify(i)

        

class Crop(ResizeCropMixin, Format):
    '''Resize and maybe re-format an image.
    A base class e.g.
        class Large(image.Crop):
            width=513
            height=760 
            tpe='png'
    '''
    def modify(self, lib_image):
        i = image_ops_pillow.crop(
            lib_image,
            self.width,
            self.height
        )
        return super().modify(i)

                
                                    
class ResizeSmart(ResizeCropSmartMixin, Format):
    '''Resize an image.
    This resize lays the image on a background of ''fill-color'.
    So the result always matches the given sizes.
    A base class e.g.
        class Large(image.ResizeSmart):
            width=513
            height=760    
            tpe='png'
            fill_color="dark-green"
    '''
    def modify(self, lib_image):
        i = image_ops_pillow.resize_aspect(
            lib_image, 
            self.width, 
            self.height
            )
        i = super().modify(i)
        i = image_ops_pillow.fill(
            i, 
            self.width, 
            self.height, 
            self.fill_color
            )
        return i




class CropSmart(ResizeCropSmartMixin, Format):
    '''Resize and maybe re-format an image.
    A base class e.g.
        class Large(image.CropSmart):
            width=513
            height=760    
            tpe='png'
            fill_color="coral"
    '''
    def modify(self, lib_image):
        i = image_ops_pillow.crop(
            lib_image, 
            self.width, 
            self.height
            )
        i = super().modify(i)
        i = image_ops_pillow.fill(
            i, 
            self.width, 
            self.height, 
            self.fill_color
            )        
        return i
