from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from pathlib import Path


class ModelUniqueFilenameMixin:

    def validate_unique(self, exclude=None):
        filepath = Path(self.upload_dir) / self.src.name
        qs = self.__class__._default_manager.filter(src=filepath)
        if qs.exists():
            raise ValidationError({'src': _('Fileename exists in image repository')})
        super().validate_unique(exclude)
