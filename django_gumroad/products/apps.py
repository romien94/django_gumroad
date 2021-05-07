from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ProductsConfig(AppConfig):
    name = 'django_gumroad.products'
    verbose_name = _('Products')
