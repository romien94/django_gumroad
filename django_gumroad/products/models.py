from django.db import models
from django.urls import reverse


class Product(models.Model):
    CALLS_TO_ACTION = (
        ('I want this', 'I want this'),
        ('Buy this', 'Buy this'),
        ('Pay', 'Pay'),
    )
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField()
    cover = models.ImageField(upload_to='product_covers/', null=True, blank=True,)
    call_to_action = models.CharField(max_length=20, choices=CALLS_TO_ACTION)
    summary = models.CharField(max_length=255, null=True, blank=True)
    content_url = models.URLField(null=True, blank=True)
    content_file = models.FileField(upload_to='product_files/', null=True, blank=True)
    price = models.DecimalField(default=10, decimal_places=2, max_digits=10)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:product-detail', kwargs={'slug': self.slug})

    def get_edit_url(self):
        return reverse('products:product-update', kwargs={'slug': self.slug})

    def get_delete_url(self):
        return reverse('products:product-delete', kwargs={'slug': self.slug})

    def get_price_in_cents(self):
        return int(self.price * 100)


class PurchasedProduct(models.Model):
    email = models.EmailField()
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    date_purchased = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
