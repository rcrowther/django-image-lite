from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from image_lite.models import AbstractImage


## These utils can only be loaded when Django/the app is ready
#? could use django.utils.module_loading.import_string()
def get_model(model_path, app_name=''):
    '''
    Get a model from a string path.
    
    model_path
         a strin path in form 'app_name.model_name'
    app_name
        an app name. If the model_path will only parse to a model, this 
        is used to provide the app name.
    return
        a model, or ImproperlyConfigured
    '''
    model_path_elements = model_path.split('.', 1)
    if (len(model_path_elements) == 1):
        if (not app_name):
            raise ImproperlyConfigured("Unable to parse model path (short name, no app data): '{}'".format(model_path))
        else:
            an = app_name            
            if callable(app_name):
                an = app_name()
            mn = model_path_elements[0]
    if (len(model_path_elements) == 2):
        an = model_path_elements[0]
        mn = model_path_elements[1]
    if (len(model_path_elements) > 2):
        raise ImproperlyConfigured("Unable to parse given model path: '{}'".format(model_path))
    try:
        Model = apps.get_model(an, mn)
    except Exception as e:
        raise ImproperlyConfigured("Unable to locate model from model path: '{}'".format(model_path))
    return Model

def get_image_model(model_path, app_name=''):
    '''
    Get an model from a string path.

    model_path
         a string path in form 'app_name.model_name'
    app_name
        an app name. If the model_path will only parse to a model, this 
        is used to provide the app name.
    return
        if path empty, Image, if path, an Image model, if path fails, 
        ImproperlyConfigured
    '''
    Model = get_model(model_path, app_name)
    if (not issubclass(Model, AbstractImage)):
        raise ImproperlyConfigured("Given class not a subclass of AbstractImage: '{}'".format(
            model_path
        ))
    return Model

