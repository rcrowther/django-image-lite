from contextlib import contextmanager
from pathlib import Path
from django.db import models, transaction
from django.core.checks import Error, Warning
#from django.urls import reverse
from django.core.files.images import ImageFile
from django.apps import apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from image_lite import checks
from image_lite.model_fields import ImageLiteField
from image_lite import registry



class SourceImageIOError(IOError):
    """
    Custom exception to distinguish IOErrors that were thrown while opening the source image
    """
    pass
    

def get_image_upload_to(instance, filename):
    """
    Obtain a valid upload path for an image file.
    This needs to be a module-level function so that it can be 
    referenced within migrations, but simply delegates to the 
    `get_upload_to` method of the instance, so that AbstractImage
    subclasses can override it.
    """
    return instance.get_upload_to(filename)
    


class AbstractImage(models.Model):
    '''
    Data about stored images.
    
    Provides db fields for width, height, bytesize and upload_data. 
    These replace storage backend ingenuity with recorded data.
    Also provides accessors for useful derivatives such as 'alt' and 
    'url'.
    
    Handles upload_to in a configurable way, and also provides 
    machinery for Reform handling.
    
    A note on configuration. An Image or Reform is always expected to 
    point at a file, it is never null. To not point at a file is an 
    error---see shortcuts and 'broken image'. Whatever model keys an 
    Image/Reform is still free to be null.
    
    An Images/Reform model is locked to a file folder. New models, even 
    if given files from the same folder, are file-renamed by Django. 
    Thus each file is unique, and each file field in the model is 
    unique.  
    '''
    # relative to MEDIA_ROOT
    upload_dir='originals'

    # 100 is Django default
    # Same as max_length on the src field, but this setting 
    # overrides that. This setting is checked to be between 1 and 
    # sixteen bits. Nut bear in mind length represents codepoints, so 
    # 20,000 codepoints is a large field for the database to store.
    # PS. Win32 operating systems can handle 255 char path lengths
    filepath_length=100
    
    # limit the unload filename length by checking on generated forms.
    # (if false, all filenames are accepted then truncated if necessary)
    form_limit_filepath_length=True
    
    # List of formats accepted. Should be lower-case, short form.
    # If None, any format recognised by this app as an image.
    accept_formats = None
    
    # If None, any size allowed. In MB. Real numbers allowed.
    max_upload_size = 2
    
    filters = []
    
    #  on DB record deletion, delete originals.
    auto_delete_upload_file=False
    
    ## Reform options ##
    # Reforms naturally inherit filename options
    reform_dir='reforms'
    
    # Add suffix of filter name to filepaths.
    # Usually, this is true. But if only one filter is defined, 
    # explicitly, it can be set false.
    filter_suffix = True
    
    
    def delete_file_and_reforms(self):
        '''
        Delete files, original and reforms, associated with this model.
        Reform removal is by constructed paths, so reasonably efficient,
        but will not repair changed filters. Failure to delete reforms
        is ignored.
        '''
        # Delete reforms
        cls = self.__class__
        fname = self.filename
        reform_file_path = cls.reform_dir_path()
        reform_file_subpath = reform_file_path
        first = True
        for filter_class in cls.get_filters():
            if (not(first)):
                reform_file_subpath =  Path(reform_file_path) / filter_class.classname_as_path_segment()                
            first = False

            #  make up full filepath
            reform_path = Path(reform_file_subpath) / (fname + '.' + filter_class.format)
            reform_path.unlink(missing_ok=True)
            
        # delete original
        # NB False =
        # "The optional save argument controls whether or not the model 
        # instance is saved after the file associated with this field 
        # has been deleted. Defaults to True."
        if (self.auto_delete_upload_file):
            self.src.delete(False)            
            
    @classmethod
    def delete_file(cls, instance, **kwargs):
        transaction.on_commit(lambda: instance.delete_file_and_reforms())

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        models.signals.post_delete.connect(cls.delete_file, sender=cls)
          
    upload_time = models.DateTimeField(_("Datetime of upload"),
        auto_now_add=True, editable=False
    )

    # A note about the name. Even if possible, using the word 'file'
    # triggers my, and probably other, IDEs. Again, even if possible,
    # naming this the same as the model is not a good idea, if only due 
    # to confusion in relations, let alone stray attribute manipulation 
    # in Python code. So, like HTML, it is 'src'     
    src = ImageLiteField(_('image_file'), 
        #storage = FileSystemStorage,
        unique=True,
        upload_to=get_image_upload_to, 
        width_field='width', 
        height_field='height',
        bytesize_field="bytesize",
    )
    
    # Django can use Pillow to provide width and height. So why?
    # The 'orrible duplication, which Django supports, is to spare web 
    # hits on remote storage, and opening and closing the file for data. 
    # Sure, the values could be cached, but here assuming code needs
    # a solid record.
    width = models.PositiveIntegerField(verbose_name=_('width'), editable=False)
    height = models.PositiveIntegerField(verbose_name=_('height'), editable=False)

    # See the property
    bytesize = models.PositiveIntegerField(null=True, editable=False)

    def is_local(self):
        """
        Is the image on a local filesystem?
        return
            True if the image is hosted on the local filesystem
        """
        try:
            self.src.path
            return True
        except ValueError as e:
            # The access attempt will fail with currently a ValueError
            # if no associated file. But in context of asking 'is it 
            # local?' that's now a source error.
            raise SourceImageIOError(str(e))
        except NotImplementedError:
            # if not local storage, return false
            return False

    def get_upload_to(self, filename):
        # Incoming filename comes from upload machinery, and needs 
        # path appending.
        return Path(self.upload_dir) / filename
        
    @contextmanager
    def open_src(self):
        # Open file if it is closed
        close_src = False
        try:
            src = self.src

            if self.src.closed:
                # Reopen the file
                if self.is_local():
                    self.src.open('rb')
                else:
                    # Some external storage backends don't allow reopening
                    # the file. Get a fresh file instance. #1397
                    storage = self._meta.get_field('src').storage
                    src = storage.open(self.src.name, 'rb')

                close_src = True
        except IOError as e:
            # IOError comes from... an IO error. 
            # re-throw these as a SourceImageIOError
            # so that calling code
            # can distinguish these from IOErrors elsewhere in the 
            # process e.g. currently causes a broken-image display.
            raise SourceImageIOError(str(e))

        # Seek to beginning
        src.seek(0)
        try:
            yield src
        finally:
            if close_src:
                src.close()

    @classmethod
    def reform_dir_path(cls):
        location = cls._meta.get_field('src').storage.location  
        path = Path(location) / cls.reform_dir
        if (not(path.is_dir())):
            raise CommandError(f"Reform path not recognised as a directory. path: '{path}'")
        return path 
    
    @classmethod
    def get_filters(cls):
        '''
        Returns a list of Filter classes available on this model.
        Returns declared filters. If no filters declared, every filter.
        '''
        filters = registry(cls)
        
        # 'filter' filters if filternames explicitly declared
        # (the default is to load them all)
        if (cls.filters):
            filters = [f for f in filters if f.name() in cls.filters]
        return filters

    @classmethod
    def get_filter(cls, filter_name):
        '''
        Returns a Filter class configured on this model, or None.
        '''
        class_list = registry(cls)
        r = None
        for k in class_list:
            if (k.__name__ == filter_name):
                r = k
                break
        return r
        
    def save(self, *args, **kwargs):
        # use save
        # Won't work for bulk creates, but niether will signals
        # https://docs.djangoproject.com/en/3.2/topics/db/models/#overriding-model-methods
        super().save(*args, **kwargs)

        # make a base path and filename
        reform_base_path = Path(settings.MEDIA_ROOT) / self.reform_dir
        
        # first write will be to the reform_base_path
        # (subsequent to subdirectories)
        reform_file_subpath = reform_base_path

        # asset the directory
        reform_file_subpath.mkdir(parents=True, exist_ok=True)
            
        # Get basic filename
        #?! why all this protection, for remotes?
        fname = str(Path(self.filename).stem)
        
        # run filters on file 
        filters = self.get_filters()
        
        # 'filter' filters if filternames explicitly declared
        # (the default is to load them all)
        if (self.filters):
            filters = [f for f in filters if f.name() in self.filters]

        #print(str(filters))
        #! firsr filter result goes in reform_base_path
        # later ones go in subfolder named after the filter
        first = True
        for filter_class in filters:
            if (not(first)):
                reform_file_subpath =  Path(reform_base_path) / filter_class.classname_as_path_segment()
                
                # asset the directory
                reform_file_subpath.mkdir(parents=True, exist_ok=True)  
            first = False
 
            #  make up full filepath
            reform_path = Path(reform_file_subpath) / (fname + '.' + filter_class.format)
                
            # get filtered buffer
            with self.src.open() as fsrc:
                filter_instance = filter_class()
                (reform_buff, iformat) = filter_instance.process(
                    fsrc,
                    #model_args
                    {}
                )
                
            with open(reform_path, "wb") as f:
                f.write(reform_buff.getbuffer())
            
            first = False
            
    # Delete is not enabled because:
    # "Note that the delete() method for an object is not necessarily 
    # called when deleting objects in bulk using a QuerySet"
    # And this class wants that to happen. The option is offered. 
    #def delete(self, *args, **kwargs):
        #pass
        
    @property
    def filename(self):
        '''
        File as name, no path, no extension.
        Useful for admin displays, and others.
        '''
        return Path(self.src.name).stem

    # @property
    # def alt(self):
        # '''
        # String for an 'alt' field.
        # The base implementation is derived from the filepath of the 
        # uploaded file. 
        # Subclasses might override this attribute to use more refined 
        # data, such as a slug or title.
        # '''
        # return Path(self.src.name).stem + ' image'
                
    def is_portrait(self):
        return (self.width < self.height)

    def is_landscape(self):
        return (self.height < self.width)

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        name = cls.__name__.lower()
        if not cls._meta.swapped:
            errors += [
            #NB By the time of check() models are built. So all 
            # attributes exist, at least as default.
            #*checks.check_type('reform_model', cls.reform_model, str, '{}.E001'.format(name), **kwargs),
            #*checks.check_str('upload_dir', cls.upload_dir, 1, '{}.E002'.format(name), **kwargs),
            *checks.filters_configured(cls._meta.app_label, cls.filters, '{}.E003'.format(name), **kwargs),
            #*checks.check_filter_suffix(cls.filter_suffix, cls.filters, '{}.E004'.format(name), **kwargs),
            *checks.check_numeric_range('filepath_length', cls.filepath_length, 1, 65535, '{}.E005'.format(name), **kwargs),
            *checks.check_image_formats_or_none('accept_formats', cls.accept_formats,'{}.E006'.format(name), **kwargs),
            *checks.check_positive_float_or_none('max_upload_size', cls.max_upload_size, '{}.E007'.format(name), **kwargs),
            *checks.check_filternames_unique(cls.filters, '{}.E008'.format(name), **kwargs),
            ]
        return errors

    def __repr__(self):
        return "{}(upload_time: {}, src:'{}')".format(
            self.__class__.__name__,
            self.upload_time,
            self.src,
        )                

    def __str__(self):
        return self.src.name

    class Meta:
        abstract = True
        
