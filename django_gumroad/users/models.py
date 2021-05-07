from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_gumroad.products.models import Product, PurchasedProduct

import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY


class User(AbstractUser):
    """Default user for django_gumroad."""

    #: First and last name do not cover name patterns around the globe
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    stripe_customer_id = models.CharField(_("Stripe customer id"), max_length=100, blank=True, null=True)
    stripe_account_id = models.CharField(_("Stripe account id"), max_length=100)

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})


class UserLibrary(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    product = models.ManyToManyField(Product, blank=True)

    class Meta:
        verbose_name_plural = _('User libraries')

    def __str__(self):
        return self.user.email


def post_save_user_receiver(sender, instance, created, **kwargs):
    if created:
        userlibrary = UserLibrary.objects.create(user=instance)

        purchased_products = [
            purchased_product.product for purchased_product in PurchasedProduct.objects.filter(email=instance.email)
        ]

        if len(purchased_products):
            userlibrary.product.add(*purchased_products)

        stripe_account = stripe.Account.create(
            type='express'
        )

        instance.stripe_account_id = stripe_account['id']
        instance.save()


post_save.connect(post_save_user_receiver, sender=User)
