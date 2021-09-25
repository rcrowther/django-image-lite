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
    auto_delete_files=False
    
    ## Reform options ##
    # Reforms naturally inherit filename options
    reform_dir='reforms'
    
    
    def delete_file_and_reforms(self):
        '''
        Delete files, original and reforms, associated with this model.
        Reform removal is by constructed paths, so reasonably efficient,
        but will not repair changed filters. Failure to delete reforms
        is ignored.
        '''
        # Delete reforms
        cls = self.__class__
        reform_dir_path = cls.reform_dir_path() / self.filename
        for filter_class in cls.get_filters():
            reform_path = Path(filter_class.add_suffix_to_path(reform_dir_path))
            reform_path.unlink(missing_ok=True)
            
        # delete original
        self.src.delete(False)            
            
    @classmethod
    def delete_file(cls, instance, **kwargs):
        transaction.on_commit(lambda: instance.delete_file_and_reforms())

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        if (cls.auto_delete_files):
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
        Returns a list of Filter classes configured on this model.
        '''
        return registry(cls)

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
    
        # Storage does this every time for a filesave. Seems inelegant,
        # but let's follow the same path, and asset the directory
        reform_base_path.mkdir(parents=True, exist_ok=True)

        fname = str(Path(self.filename).stem)
        reform_file_path =  Path(reform_base_path) / fname
        
        # run filters on file 
        filters = self.get_filters()
        if (self.filters):
            filters = [f for f in filters if f.name() in self.filters]

        #print(str(filters))
        for filter_class in filters:
            reform_path = filter_class.add_suffix_to_path(reform_file_path)

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
            *checks.check_numeric_range('filepath_length', cls.filepath_length, 1, 65535, '{}.E003'.format(name), **kwargs),
            *checks.check_image_formats_or_none('accept_formats', cls.accept_formats,'{}.E004'.format(name), **kwargs),
            *checks.check_positive_float_or_none('max_upload_size', cls.max_upload_size, '{}.E003'.format(name), **kwargs),
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
        
