import zlib
import struct
from pathlib import Path
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from django.utils.deconstruct import deconstructible
from image_lite.constants import (
    IMAGE_FORMATS,
    EXTENSION_TO_APP_FORMAT,
    FORMAT_UCLIB_TO_APP
)

def get_pillow_attribute(file, pil_attr):
    """
    Returns an attribute from a Pillow image of the given file,
    file
        a file. wrappable by Pillow. Must be open
    pil_attr
        the attribute to read.
    return 
        the attribut, or None, if unreadaable. the file is not closed.
    """
    # This devilish, ticketed code is lifted from 
    # django.core.files.images, where it seeks image dimensions.
    # Unfortunately, that code is not configurable nor overridable.
    from PIL import ImageFile as PillowImageFile

    p = PillowImageFile.Parser()
    file_pos = file.tell()
    file.seek(0)
    try:
        # Most of the time Pillow only needs a small chunk to parse the
        # image and get data, but with some TIFF files Pillow needs to
        # parse the whole file.
        chunk_size = 1024
        while 1:
            data = file.read(chunk_size)
            if not data:
                break
            try:
                p.feed(data)
            except zlib.error as e:
                # ignore zlib complaining on truncated stream, just feed more
                # data to parser (ticket #19457).
                if e.args[0].startswith("Error -5"):
                    pass
                else:
                    raise
            except struct.error:
                # Ignore PIL failing on a too short buffer when reads return
                # less bytes than expected. Skip and feed more data to the
                # parser (ticket #24544).
                pass
            except RuntimeError:
                # e.g. "RuntimeError: could not create decoder object" for
                # WebP files. A different chunk_size may work.
                pass
            if p.image:
                return getattr(p.image, pil_attr)
            chunk_size *= 2
        return None
    finally:
        file.seek(file_pos)
            
    
@deconstructible
#class ImageFileDataConsistencyValidator:
class ImageFileExtensionValidator:
    '''
    Check the extension of an image file.
    Checks the extension against the internally defined set of file 
    extensions. Then does a Pillow read, to see what Pillow thinks,
    and compares the two.

    allowed_extensions
        a lower case, short format, list
    '''
    messages = {
        'no_extension': _(
            "No file extension. Allowed extensions: %(extensions)s."
        ),
        'extension_not_allowed': _(
            "File extension %(extension)s not allowed. allowed extensions: %(extensions)s."
        ),
        'format_not_readable': _(
            "File not readable as an image."
        ),
        'format_extension_mismatch': _(
            "Found format does not match extension."
        ),
    }
    allowed_extensions = IMAGE_FORMATS
    ext2app = EXTENSION_TO_APP_FORMAT
    pil2app = FORMAT_UCLIB_TO_APP
    
    def __init__(self, allowed_extensions=None):
        if allowed_extensions is not None:
            self.allowed_extensions = allowed_extensions
        self.allowed_extensions_message = ', '.join(self.allowed_extensions)
        
    def __call__(self, v):
        extension = Path(v.name).suffix[1:].lower()
        if (len(extension) < 2):
            raise ValidationError(
                    self.messages['no_extension'],
                    code='no_extension',
                    params={'extensions': self.allowed_extensions_message},
                )
        if (not(extension in self.allowed_extensions)):
            raise ValidationError(
                    self.messages['extension_not_allowed'],
                    code='extension_not_allowed',
                    params={'extension': extension, 'extensions': self.allowed_extensions_message},
                )
        try:
            raw_read_format = get_pillow_attribute(v.file, 'format')
        except Exception as e:
            raise ValidationError(
                    self.messages['format_not_readable'],
                    code='format_not_readable',
                ) from e
        read_format = self.pil2app[raw_read_format]
        declared_format = self.ext2app[extension]
        if (read_format != declared_format):
            raise ValidationError(
                    self.messages['format_extension_mismatch'],
                    code='format_extension_mismatch',
                )
        
    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.allowed_extensions == other.allowed_extensions
        )

def validate_image_file_consistency(value):
    return ImageFileExtensionValidator()(value)

def validate_file_size(file, max_size):
    '''
    Check size of a file.
    Must be protected from out of range values like None.
    
    max_size
        in bytes
    file
        a Django file class. The file must be open.
    '''
    # Check filesize
    if (file.size > max_size):
        raise ValidationError(
            "This file is too big* ({}). Maximum filesize {}.".format(
                filesizeformat(file.size),
                filesizeformat(max_size)
            ))
