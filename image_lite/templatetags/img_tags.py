from django import template
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt
from django.core.exceptions import ImproperlyConfigured
from django.template.base import kwarg_re
from django.conf import settings
import os

#from django.utils.functional import cached_property
from image_lite import module_utils
from image_lite import utils

register = template.Library()

def arg_unquote(a, token, arg_name):
    if not (a[0] == a[-1] and a[0] in ('"', "'")):
       raise template.TemplateSyntaxError(
            "image tag {} argument must be in quotes. tag:{{% {} %}} value:{}".format(
            arg_name,
            token.contents,
            a
       ))
       
    return a[1:-1]

def to_kwargs(token, kwlumps):
    kwargs = {}

    # Tag is tokenizing is from strings, and that depends on 
    # quotes for whitespace and separation.
    # However, the result must be quote-stripped for flatattr() to do
    # it's Django-compliant job in ImageNode.
    # (It might be nice to do further parsing on keyword values, to 
    # allow vars and so forth. But in this atmosphere...)   
    for kw in kwlumps:
        match = kwarg_re.match(kw)
        if not match:
            raise template.TemplateSyntaxError("Malformed arguments to image tag. tag:{{% {} %}} kw:{}".format(
               token.contents,
               kw
           ))
        k, v = match.groups()
        if not (v[0] == v[-1] and v[0] in ('"', "'")):
           raise template.TemplateSyntaxError(
               "image tag keyword arguments must be in quotes. tag:{{% {} %}} kw:{}".format(
               token.contents,
               kw
           ))
        kwargs[k] = v[1:-1]

    return kwargs


class GetImageNode(template.Node):
    def __init__(self, reform_dir, file_path, kwargs):
        self.reform_dir = reform_dir
        self.file_path = file_path
        self.kwargs = kwargs

    def render(self, context):
        try:
            return mark_safe('<img src="{}" {} />'.format(
                self.file_path, 
                flatatt(self.kwargs)
                ))
        except template.VariableDoesNotExist:
            return ''
                            
@register.tag(name="image_fixed")
def image_fixed_tag(parser, token):
    '''
    Generate a URL for an image. 
    
    This tag seaches for a given filename.
    
    The image model table is not searched---the model is used to gather 
    some prperties, notably the path to image files. 
    This tag is unable to use filters, because it is not looking for
    anything.

    The tag is a full tag constructor. Keywords become tag attributes,

        {% image_url review review_images.ReviewImage class="narrow" %}
    
    model_name
        reference to a AbstractImage subclass in dotted notation. Must 
        be full path relative to the project base e.g. pages.MainImage.
    
    file_name
        name of a file, without path or extension.
        
    filter_name
        Name of a filter. No need for a module path, because the filter 
        should be located with the model. 
    
    kwargs 
        Will be added as attributes to the final tag.
    ''' 
    lumps = token.split_contents()

    if(len(lumps) < 3):
        raise template.TemplateSyntaxError(
            "Image Fixed tag needs three arguments. tag:{{% {} %}}".format(
                token.contents,
            ))
            
    tag_name = lumps[0]
    model_name = lumps[1]
    file_name = lumps[2]
    filter_name = lumps[3]
    kwargs = to_kwargs(token, lumps[4:])

    # get reform dir from the image model
    im = module_utils.get_image_model(model_name)
    reform_dir = os.path.join(settings.MEDIA_URL, im.reform_dir)
    
    # extension comes from the filter
    f = im.get_filter(filter_name)     
    extension = f.format
            
    # construct an alt
    if (not 'alt' in kwargs):
        kwargs['alt'] = f"image of {file_name}"
    full_name = file_name + '-' + filter_name  + '.' + extension
    file_path = os.path.join(reform_dir, full_name)

    return GetImageNode(reform_dir, file_path, kwargs)



class ImageNode(template.Node):
    def __init__(self, reform_dir,  template_var, filename_callable, kwargs):
        self.reform_dir = reform_dir
        self.template_var = template.Variable(template_var)
        self.filename_callable = filename_callable      
        self.kwargs = kwargs
        
    def render(self, context):
        try:
            template_var = self.template_var.resolve(context)
            
            # get the basename
            file_name = getattr(template_var, self.filename_callable)()

            # construct the alt
            if (not 'alt' in self.kwargs):
                self.kwargs['alt'] = f"image of {file_name.rsplit('-', 1)[0]}"
            filepath = os.path.join(self.reform_dir, file_name)
            return mark_safe('<img src="{}" {} />'.format(
                filepath, 
                flatatt(self.kwargs)
                ))
        except template.VariableDoesNotExist:
            return ''
              
@register.tag(name="image")
def image_tag(parser, token):
    '''
    Generate a URL for an image. 
    
    This tag generates a URL by getting an image directory path, then 
    prepending that to the return from a callable (for the filename).

    The tag is a full tag constructor. Keywords become tag attributes,

        {% image_url review review_images.ReviewImage class="narrow" %}
    
    model_name
        reference to a AbstractImage subclass in dotted notation. Must 
        be full path relative to the project base e.g. pages.MainImage.

    template_var
        A template var containing the object on which the callable will
        be called. 
        
    filename_callable
        name of a method on the repository model. The method should 
        return the filename of the image, including filter and file 
        extension (the path is constructed by tag code)
    
    kwargs 
        Will be added as attributes to the final tag.
    ''' 
    lumps = token.split_contents()

    if(len(lumps) < 3):
        raise template.TemplateSyntaxError(
            "Image tag needs three arguments. tag:{{% {} %}}".format(
                token.contents,
            ))
            
    tag_name = lumps[0]
    model_name = lumps[1]
    template_var = lumps[2]
    filename_callable = lumps[3]
    kwargs = to_kwargs(token, lumps[4:])

    # get reform dir
    im = module_utils.get_image_model(model_name)
    reform_dir = os.path.join(settings.MEDIA_URL, im.reform_dir)
        
    return ImageNode(reform_dir, template_var, filename_callable, kwargs)
