from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from rest_framework.authtoken.views import obtain_auth_token

from django_gumroad.users.views import UserLibraryView, StripeAccountLinkView

from django_gumroad.products.views import (
    ProductListView,
    UserProductListView,
    ProductCreateView,
    CreateCheckoutSession,
    CheckoutSuccessView,
    stripe_webhook
)

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("django_gumroad.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    path("user-library/", UserLibraryView.as_view(), name='user-library'),
    path("discover/", ProductListView.as_view(), name='discover'),
    path("products/", UserProductListView.as_view(), name='user-products'),
    path("products/create/", ProductCreateView.as_view(), name='product-create'),
    path("create-checkout-session/<slug>/", CreateCheckoutSession.as_view(), name='create-checkout-session'),
    path("checkout/success/", CheckoutSuccessView.as_view(), name='checkout-success'),
    path("stripe/auth/", StripeAccountLinkView.as_view(), name='stripe-account-link'),
    path("webhooks/stripe/", stripe_webhook, name='stripe-webhook'),
    path("p/", include("django_gumroad.products.urls", namespace="products")),
    # Your stuff: custom urls includes go here
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router")),
    # DRF auth token
    path("auth-token/", obtain_auth_token),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
