from django.urls import path

from django_gumroad.products.views import (
    ProductDetailView,
    ProductUpdateView,
    ProductDeleteView
)

app_name = 'products'

urlpatterns = [
    path('<slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('<slug>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('<slug>/delete/', ProductDeleteView.as_view(), name='product-delete'),
]
