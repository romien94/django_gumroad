from django.contrib import admin

from django_gumroad.products.models import Product, PurchasedProduct


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


admin.site.register(PurchasedProduct)

