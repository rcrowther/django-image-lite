from collections import Iterable 
from image_lite import utils


class AlreadyRegistered(KeyError):
    pass


class NotRegistered(KeyError):
    pass
    
    
class Unregisterable(Exception):
    pass


class ClassByModuleRegistry:
    '''
    Simple registry.
    This is useful for locating code. Why do that when Python's import
    system is flexible and concise?
    Because you may wish to refer to code by string names. This is 
    relevant when code needs to be accessed from Django templates,
    where parameters are (mostly) strings.
    - Why not use a cached property?
    - Use decorators? 
    Because this allows targeted classes, so other code can be put in 
    the targetted modules.
    Does not handle permissions. 
    '''
    def __init__(self):
        # app_name -> list(class (not instance))
        self._registry = {} 



    def __contains__(self, klass):
        app_name = utils.app_name(klass)
        class_name = klass.__name__
        class_list = self._registry.get(app_name, [])
        r = False
        for k in class_list:
            r = r or (k.__name__ == class_name)
        return r
        
    def register(self, klass):
        #print(str(klass.__module__.split('.', 1)[0]))
        app_name = utils.app_name(klass)
        if (not app_name in self._registry):
            self._registry[app_name] = []
        else:
            class_list = self._registry[app_name]
            if klass in class_list:
                raise AlreadyRegistered('Already registered. class:{}'.format(
                    klass.__name__
                ))
        self._registry[app_name].append(klass)
                
    # def unregister(self, klass):
        # """
        # Unregister the given model(s).

        # If a model isn't already registered, raise NotRegistered.
        # """
        # if k not in self._registry:
            # raise NotRegistered('Class can not be unregistered {}'.format(k))
        # del self._registry[k]

    def value_by_name(self, app_name):
        try:
            r = self._registry[app_name]
        except KeyError:
            raise NotRegistered("Module entries requested but not found. app_name:{}".format(
            app_name
            ))
        return r
                
    def __call__(self, klass_or_instance):
        '''
        A list of classes registered in the module.
        '''
        r = None
        app_name = utils.app_name(klass_or_instance)
        return self.value_by_name(app_name)
        

                
    @property
    def list_apps(self):
        return self._registry.keys()

    def list_entries(self):
        r = []
        for l in self._registry.values():
            r.extend(l)
        return r
        
    @property
    def size(self):
        return len(self._registry)    
        
    def __str__(self):
        r = []
        for app_name, class_list in self._registry.items():
            #class_nameB = []
            #print(str(class_list))
            #for klass in class_list:
            #    class_nameB.append(klass.__name__)
            class_nameB = [klass.__name__ for klass in class_list]
            class_names = ", ".join(class_nameB) 
            #print(str(nameList))
            r.append( f"{app_name}=>({class_names})" )
        class_list_by_app = ", ".join(r) 
        return f"{self.__class__.__name__}({class_list_by_app})"
        
from image_lite.filters import Filter

class FilterRegistry(ClassByModuleRegistry):
    def register(self, class_or_iterable):
        if (not isinstance(class_or_iterable, Iterable)):
            class_or_iterable = [class_or_iterable]
        for filter_class in class_or_iterable:
            if (not (issubclass(filter_class, Filter))):
                raise Unregisterable("Class is not a subclass of Filter. class:{}".format(
                    filter_class.__path__
                ))
            super().register(filter_class)

    def get_filter(self, app_name, filter_name):
        class_list = self._registry.get(app_name, [])
        r = None
        for k in class_list:
            if (k.__name__ == filter_name):
                r = k
                break
        return r
        
    def registered_names(self, app_name):
        class_list = super().value_by_name(app_name)
        return [f.name() for f in class_list]
    # def unregister(self, class_or_iterable):
        # if (not isinstance(class_or_iterable, Iterable)):
            # class_or_iterable = [class_or_iterable]
        # for filter_class in class_or_iterable:
            # super().unregister(filter_class)
      
registry = FilterRegistry()
