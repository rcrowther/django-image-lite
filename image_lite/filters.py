from image_lite import checks



class PlacementError(Exception):
    """
    Custom exception for attempted registration of Filters not in an 'image_filers' module
    """
    pass


        
class Filter():
    '''
    A filter defines how to transorm a image with a spec into 
    a derivative with a different spec.
    As such, it is more than a static configuration. It is half-
    functional. takes an open Python file and returns a buffer. 
    The stock implementation uses Pillow, but this setup allows 
    other codebases to bue used in a filler without changing calling 
    code.
    '''
    #? cache
    @classmethod
    def _module_path_human(cls):
        ''' 
        Human readable module path.
        Used to refer to a filter in the registry and templates. 
        Currently based on the module path and classname.
        '''
        mp = cls.__module__.split('.')
        
        # We encourage users to place filters in a 
        # module called image_filters'. This would involve a lot of
        # repetition in template code. So an 'image_filters' element is removed from the path.
        # That risks a collision with
        # filters placed in the root of an app, so insist on placement in 'image filters'.
        if (mp[-1] == 'image_filters'):
            del(mp[-1])
        else:
            raise PlacementError("Please locate Filters to be registered in an 'image filters' module: {}.{}".format(
                cls.__module__,
                cls.__name__
            ))        
        return mp
        
    @classmethod
    def name(cls):
        return cls.__name__
        
    @classmethod
    def human_id(cls):
        ''' 
        id for the filter.
        Used to refer in the registry and templates, so is human 
        readable. 
        Currently based on a dotted module path and classname.
        '''
        p = cls._module_path_human()
        p.append( cls.__name__ )
        
        # That is unique, but we encourage users to place filters in a 
        # module called image_filters'. This would involve a lot of
        # repetition in template code. At the risk of a collision with
        # filters placed in the root of an app, we remove that part of 
        # the path.
        return ".".join(p)
        
    #x unused?
    def filename(self, stem, extension):
        '''
        Generate a filename from a base string.
        An ammended filter path and name is appended to the stem,
        
        stem + '-' + ammended underscore path + '_' + filtername.lower() + '.' + extension
         
        It is to be concise, and near-unique to avoid provoking storage backends, 
        '''
        return "{}-{}_{}.{}".format(
            stem,
            "_".join(self._module_path_human()),
            type(self).__name__.lower(),
            extension
        )
        
    @classmethod
    def check(cls, **kwargs):
        return []

    def process(self, src_file, model_args):
        '''
        Wrap a Python file handle for processing a reform.
        Return should be a BytesIO buffer or similar. Some APIs do not
        include file saving, but most will deal with a generic Python
        buffer.
                 
        'save_info_callback' makes decisions about how the resulting 
        buffer should be saved. There is no need to call this function 
        for dev, but final versions should respect the environment by 
        calling it and acting on the results. Current implementation 
        needs the source format, then checks with overall and filter 
        settings, then returns decisions on 'format' and 'jpeg_quality'.
                
        src_file 
            an open Python file handle 
        return 
            a BytesIO or similar
        '''
        raise NotImplementedError
        
        
        
# Classes here on are mixins. They estabish attributes and checks, 
# skeletons to hang image-processing code on.
class FormatMixin():
    '''Establish the format for an image. 
    Set format=None means the image is unchanged.
    Most filters will contain and build from this base class.
    '''
    format=None
    jpeg_quality=None
    
    @classmethod
    def add_suffix_to_path(cls, base_path):
        return str(base_path) + '-' + cls.__name__ + '.' + cls.format
        
    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        errors += [
            *checks.check_image_format_or_none('format', cls.format, 'image_filter.E001', **kwargs),
            *checks.check_jpeg_has_quality( cls.format, cls.jpeg_quality, 'image_filter.E002', **kwargs),
            *checks.check_jpeg_quality_range(cls.jpeg_quality, 'image_filter.E003', **kwargs),
            *checks.check_jpeg_legible(cls.jpeg_quality, 'image_reform.W001', **kwargs),
        ]
        return errors


class PhotoFXMixin():
    '''Establish the format for an image. 
    Set format=None means the image is unchanged.
    Most filters will contain and build from this base class.
    '''
    pop=False
    greyscale=False    
    night=False
    warm=False
    strong=False
    film=False
    no=False
    watermark=''
    
    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        errors += [
            *checks.check_boolean('pop', cls.pop, 'image_filter.E003', **kwargs),
            *checks.check_boolean('greyscale', cls.greyscale, 'image_filter.E004', **kwargs),
            *checks.check_boolean('night', cls.night, 'image_filter.E005', **kwargs),
            *checks.check_boolean('warm', cls.warm, 'image_filter.E006', **kwargs),
            *checks.check_boolean('strong', cls.strong, 'image_filter.E007', **kwargs),
            *checks.check_boolean('film', cls.film, 'image_filter.E008', **kwargs),
            *checks.check_boolean('no', cls.no, 'image_filter.E009', **kwargs),
            #NB Would test for watermark existance, but it is URL access,
            # thus server dependant.
        ]
        return errors
        
                           
                                
class ResizeCropMixin():
    '''Resize n image.
    Shrinks inside the box defined by the given args. So the result will
    usually be smaller width or height than the given box.
    A base class.
    '''
    width = None
    height = None
    
    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        errors += [
            *checks.check_positive('width', cls.width, 'image_filter.E011', **kwargs),
            *checks.check_positive('height', cls.height, 'image_filter.E012', **kwargs),
        ]
        return errors
        
                                    
class ResizeCropSmartMixin(ResizeCropMixin):
    '''Resize an image.
    This resize lays the image on a background of ''fill-color'.
    So the result always matches the given sizes.
    A base class
    '''
    fill_color="white"

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        errors += [
        #? No test for color
        ]
        return errors
