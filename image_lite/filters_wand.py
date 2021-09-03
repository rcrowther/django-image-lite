from wand.image import WandImage
from io import BytesIO
from image_lite.filters import (
    Filter,
    FormatMixin,
    PhotoFXMixin,
    ResizeCropMixin,
    ResizeCropSmartMixin,
)
from image_lite import image_ops_wand
from image_lite.constants import FORMAT_APP_TO_UCLIB, FORMAT_UCLIB_TO_APP
from image_lite.decisions import reform_save_info



class WandProcess():

    def process(self, src_file, model_args):
        image = WandImage(file=src_file)
 
        # write_attrs currently {format, jpeg_quality}
        write_attrs = reform_save_info(
                    self,
                    FORMAT_UCLIB_TO_APP[image.format],
                    model_args,
                    )
 
        # break out processing, it's the only action that changes
        # across different filters
        wand_dst = self.modify(image) or image
        
        # set the format
        wand_dst.format = FORMAT_APP_TO_UCLIB[write_attrs['format']]
        
        # set JPEG and others quality
        wand_dst.compression_quality = write_attrs['jpeg_quality']
        
        # Defend against rendering jpeg transparency
        if ((wand_dst.alpha_channel) and (write_attrs['format'] == 'jpg')): 
            # Here's where Wand plays for us. Alpha channel or not, it 
            # sets a background_color. And the default is 'white', like 
            # us. So all we have to do is remove the alpha channel, 
            # because Wand doesn't like one on jpeg rendering, and Wand 
            # will compose down.
            wand_dst.alpha_channel = 'remove'
        out_buff = BytesIO()

        wand_dst.save(
            out_buff,
        )
        
        return (out_buff,  write_attrs['format'])

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
        # Wand often alters in-place, but generates images for some 
        # processing.
        return lib_image



class Format(PhotoFXMixin, FormatMixin, WandProcess, Filter):
    '''Establish the format for an image. 
    Set iformat=None means the image is unchanged.
    '''
    def modify(self, lib_image):
        return image_ops_wand.photoFX(
            lib_image, 
            self.pop, 
            self.greyscale, 
            self.warm, 
            self.night, 
            self.strong, 
            self.no,
            self.watermark,
        )    


                        
class Resize(ResizeCropMixin,  Format):
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
        i = image_ops_wand.resize_aspect(
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
        i = image_ops_wand.crop(
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
        i = image_ops_wand.resize_aspect(
            lib_image, 
            self.width, 
            self.height
            )
        i = super().modify(i)
        i = image_ops_wand.fill(
            lib_image, 
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
        i = image_ops_wand.crop(
            lib_image, 
            self.width, 
            self.height
            )
        i = super().modify(i)
        i = image_ops_wand.fill(
            lib_image, 
            self.width, 
            self.height, 
            self.fill_color
            )        
        return i
