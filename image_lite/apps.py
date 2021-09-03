from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.core import checks
from image_lite.checks import check_filters


class ImageLiteConfig(AppConfig):
    # NB It would be custom to test for operation of depend libraries
    # here, primarily Pillow. However, Django now does this for 
    # ImageFile. Also, the Wand files are a boxed and optional import. 
    # So not a concern.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'image_lite'
    verbose_name = _("Image handling")
    

    def ready(self):
        super().ready()
        self.module.autodiscover()   
        checks.register(check_filters, 'image_filters')
