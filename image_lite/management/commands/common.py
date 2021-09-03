from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError
from image_lite import module_utils
from pathlib import Path


def add_model_argument(parser):
        parser.add_argument(
            'model',
            type=str,
            help='Target a model derived from AbstractImage, form:is <app.model>.',
        )
        
def get_image_model(options):
    model_path = options['model']        
    try:
        Image = module_utils.get_image_model(model_path)
    except ImproperlyConfigured as e:

        # Stock exception system not working for this
        raise  CommandError(e.args[0])
    return Image

def get_storage(image_class_or_instance):
    return image_class_or_instance._meta.get_field('src').storage 

def get_reform_path(options):
    im = get_image_model(options)
    #! use im.reform_dir_path()
    storage = im._meta.get_field('src').storage   
    path = Path(storage.location) / im.reform_dir
    if (not(path.is_dir())):
        raise CommandError(f"Reform path not recognised as a directory. path: '{path}'")
    return path 
            
def add_contains_argument(parser):
    parser.add_argument(
        '-c',
        '--contains',
        type=str,
        help='Search for src-names containing this text',
    )
    
def filter_query_contains(options, queryset):
    if (options["contains"]):
        queryset = queryset.filter(src__icontains=options["contains"])
    return queryset
