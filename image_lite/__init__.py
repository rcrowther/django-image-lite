"""Local image handling for Django. Unobtusive, with multiple repositories, powerful filter system and scaleable data."""
__version__ = '0.1.2'

from image_lite.decorators import register
from image_lite.filters import Filter
from image_lite.registry import registry
from image_lite.module_loading import autodiscover_modules
from image_lite.model_mixins import ModelUniqueFilenameMixin


# This is placed here as a convenient point, not because it runs on 
# init.
# autodiscover_modules does a hairy import, which will 
# fail on Django initialisation, so this method is is run from 
# ImageConfig in apps.py
def autodiscover():
    autodiscover_modules(
        'image_filters', 
        parent_modules = [], 
        find_in_apps = True, 
        not_core_apps = True
    )
