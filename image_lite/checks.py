from django.core import checks
from image_lite.constants import IMAGE_FORMATS



# Needs clearout
## This app specific
def check_filters(**kwargs):
    '''
    Check registered filters with Django static checks framework.
    '''
    from image_lite import registry
    errors = []
    #print(str(registry))
    for filter_class in registry.list_entries():
        #print(str(filter_class))
        filter_instance = filter_class()
        errors.extend(filter_instance.check())
    return errors


def _image_format_error(setting_name, v, eid, accepted_formats):
    return checks.Error(
                "'{}' format '{}' unrecognised."
                " Recognised image formats: {}".format(
                setting_name,
                v,
                ", ".join(accepted_formats),
            ),
            id=eid,
    )
    
def check_image_format_or_none(
        setting_name,
        image_format,
        eid, 
        accepted_formats=IMAGE_FORMATS,
        **kwargs
    ):
    '''
    Accepts a format
    '''
    errors = []
    if (image_format is None):
        return errors
    if (not(image_format in accepted_formats)):
        errors.append(_image_format_error(setting_name, v, eid, accepted_formats))
    return errors 
    
def check_image_formats_or_none(
        setting_name, 
        image_formats,
        eid, 
        accepted_formats=IMAGE_FORMATS,
        **kwargs
    ):
    '''
    Accepts a list of formats
    '''
    errors = []
    if (image_formats is None):
        return errors
    unrecognised_formats = [f for f in image_formats if not(f in accepted_formats)]
    if (unrecognised_formats):
        v = ", ".join(unrecognised_formats)
        errors.append(_image_format_error(setting_name, v, eid, accepted_formats))
    return errors 
    
def check_jpeg_has_quality(img_format, jpeg_quality, eid, **kwargs):
    errors = []
    if (img_format == 'jpg' and (not jpeg_quality)):
        errors.append(
            checks.Error(
                "If format is 'jpg' then 'jpeg_quality' must be declared.",
                id=eid,
            ))   
    return errors  
    
def check_jpeg_quality_range(jpeg_quality, eid, **kwargs):
    errors = []
    if (jpeg_quality and (jpeg_quality < 1 or jpeg_quality > 100)):
        errors.append(
            checks.Error(
                "'jpeg_quality' value '{}' must be 1--100.".format(
                jpeg_quality
            ),
            id=eid,
        ))   
    return errors  

def check_jpeg_legible(jpeg_quality, eid, **kwargs):
    errors = []
    if (jpeg_quality and (jpeg_quality < 12)):
        errors.append(
            checks.Warning(
                "'jpeg_quality' value '{}' is very low.".format(
                jpeg_quality
            ),
            id=eid,
        ))   
    return errors 

def filters_configured(app_name, filters, eid, **kwargs):
    from image_lite.registry import registry

    errors = []
    available_filters = registry.registered_names(app_name)
    for fname in filters:
        if (not(fname in available_filters)):
            errors.append(
                checks.Error(
                    "'filter' value '{}' is not in filter registry.".format(
                    fname
                ),
                id=eid,
            ))      
    return errors 
    
## General
def check_is_subclass(setting_name, v, base_klass, eid, **kwargs):
    errors = []
    if (not(issubclass(v, base_klass))):
        errors.append(
            checks.Error(
                "''{}' value {} must be a subclass of {}.".format(
                setting_name,
                v,
                base_klass.__name__,
            ),
            id=eid,
        ))
    return errors
    
def check_type(setting_name, v, tpe, eid, **kwargs):
    errors = []
    if (not(type(v)==tpe)):
        errors.append(
            checks.Error(
                "'{}' value '{}' must be type {}.".format(
                setting_name, 
                v,
                tpe
            ),
            id=eid,
        ))
    return errors 

def check_boolean(setting_name, v, eid, **kwargs):
    return check_type(setting_name, v, bool, eid, **kwargs)

def check_int(setting_name, v, eid, **kwargs):
    return check_type(setting_name, v, int, eid, **kwargs)
        
def check_positive(setting_name, v, eid, **kwargs):
    errors = check_int(setting_name, v,  eid, **kwargs)
    if ((not errors) and int(v) <= 0):
        errors.append(
            checks.Error(
            "'{}' value '{}' must be a positive number.".format(
            setting_name, 
            v
            ),
            id=eid,
        ))
    return errors 

def check_positive_float_or_none(setting_name, v, eid, **kwargs):
    errors = []
    if (v is None):
        return errors
    try:
        if (float(v) <= 0):
            raise TypeError
    except TypeError:    
        errors.append(
            checks.Error(
            "'{}' value '{}' must be None or a positive float.".format(
            setting_name, 
            v
            ),
            id=eid,
        ))
    return errors
             
def check_numeric_range(setting_name, v, imin, imax, eid, **kwargs):
    errors = []
    try:
        if (type(v) != int or v < imin or v > imax):
            raise TypeError
    except TypeError: 
        errors.append(
            checks.Error(
                "'{}' value '{}' must be > {} and < {}.".format(
                setting_name, 
                v,
                imin,
                imax,
                ),
                id=eid,
        ))
    return errors

# def check_file_exists(setting_name, v, eid, **kwargs):    
    # errors = []
    # if (v and (not(Path(v).is_file()))):
        # errors.append(
            # checks.Error(
            # "'{}' value '{}' can not be deetected as an existing file".format(
            # setting_name, 
            # v
            # ),
            # id=eid,
        # ))
    # return errors 

    # def _check_available_filelength(cls, **kwargs):
        # '''
        # Does filepath_length allow for filenames?
        # '''
        # errors = []
        # print(str(cls.filepath_length))
        # declared_len = int(cls.filepath_length)
        # path_len =  len(cls.upload_dir)
        # if (declared_len <= path_len):
            # errors.append(
                # Error(
                    # "'filepath_length' must exceed base path length. 'filepath_length' len: {}, 'upload_dir' len: {}".format(
                     # declared_len,
                     # path_len,
                     # ),
                    # id='image_model.E002',
                # )
            # )
        # elif (declared_len <= (path_len + 12)):
            # errors.append(
                # Warning(
                    # "Less than 12 chars avaiable for filenames. 'filepath_length' len: {}, 'upload_dir' len: {}".format(
                     # declared_len,
                     # path_len,
                     # ),
                    # id='image_model.W001',
                # )
            # )
        # return errors
