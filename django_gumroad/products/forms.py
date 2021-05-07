from django import forms

from django_gumroad.products.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ('user', )
