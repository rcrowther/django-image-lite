import math
from django.utils.functional import cached_property
from django.templatetags.static import static


def app_name(klass):
    '''
    Get an app name from a klass
        return the appname. IF the name is empty, it returns empty
    '''
    # appears to be the most complete way of getting an appname.
    # Doesn't rely on, for example, the class being a package
    r = klass.__module__.split('.', 1)[0]
    if (r == ""):
        raise Exception(f"App name requested but not found. klass:{klass}")
    return r
            
def bytes2mb(v):
    # This is how Django does it, I think, binary MB
    #NB must handle fractions so not shifts
    return v / 1048576

def mb2bytes(v):
    # This is how Django does it, I think, binary MB
    #NB must handle fractions so not shifts
    return math.ceil(v * 1048576)

def url_absolute_static_aware(path):
    """
    Given a relative or absolute path to a static asset, return an 
    absolute path. 
    
    return
        An absolute path will be returned unchanged while a 
        relative path will be passed to 
        django.templatetags.static.static(). This prefixes with 
        STATIC_URL or a staticfiles_storage.storage defined prefix 
        (usually '/static/').
    """
    # Straight lift from django.forms.widgets.Media
    if path.startswith(('http://', 'https://', '/')):
        return path
    return static(path)

#! Where, and for what?
# from django.utils.encoding import iri_to_uri
# from urllib.parse import quote, urljoin
# from django.conf import settings


#! should match names with pathlib.Path
# class ModulePath():
    # '''
    # Path-like class for handling import/module patths.
    # '''
    # @classmethod
    # def from_str(class_object, str_path):
        # '''Call as
           # d = ModulePath.from_str('graphic.effect.zoom')
        # '''
        # return class_object(*str_path.split('.'))
        
    # def __init__(self, *args):
        # self.path = args

    # @property
    # def size(self):
        # return len(self.path)
        
    # @property
    # def leaf(self):
        # return self.path[-1]
               
    # @property
    # def root(self):
        # return self.path[0]
        
    # @property
    # def branch(self):
        # if (self.size > 1):
            # return ModulePath(*self.path[0:-1])
        # else:
            # raise IndexError('Can not return branch when length is one. elem:{}'.format(root))
            
    # def extend(self, new_leaf):
        # return ModulePath(*self.path, new_leaf)
        
    # @property
    # def str(self):
        # return self.__str__()
        
    # def __repr__(self):
        # return 'ModulePath("{}")'.format('", "'.join(self.path))
        
    # def __str__(self):
        # return ".".join(self.path)
        

