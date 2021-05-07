from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import reverse
from django.conf import settings
from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail

import stripe
from stripe.error import SignatureVerificationError

from django_gumroad.products.models import Product, PurchasedProduct
from django_gumroad.users.models import User, UserLibrary
from django_gumroad.products.forms import ProductForm


stripe.api_key = settings.STRIPE_SECRET_KEY


class ProductListView(generic.ListView):
    model = Product
    queryset = Product.objects.filter(active=True)
    template_name = 'discover.html'
    context_object_name = 'products'


class ProductDetailView(generic.DetailView):
    model = Product
    queryset = Product.objects.all()
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        has_access = False
        user = self.request.user
        product = self.get_object()
        if user.is_authenticated:
            if product in user.userlibrary.product.all():
                has_access = True
        context.update({
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
            'has_access': has_access
        })
        return context


class ProductCreateView(LoginRequiredMixin, generic.CreateView):
    form_class = ProductForm
    template_name = 'products/product_create.html'

    def get_success_url(self):
        return reverse('products:product-detail', kwargs={'slug': self.product.slug})

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.user = self.request.user
        instance.save()
        self.product = instance
        return super(ProductCreateView, self).form_valid(form)


class ProductUpdateView(LoginRequiredMixin, generic.UpdateView):
    form_class = ProductForm
    template_name = 'products/product_update.html'
    success_url = reverse_lazy('user-products')
    context_object_name = 'product'

    def get_success_url(self):
        return reverse('products:product-detail', kwargs={'slug': self.get_object().slug})

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)


class ProductDeleteView(LoginRequiredMixin, generic.DeleteView):
    success_url = reverse_lazy('user-products')
    template_name = 'products/product_delete.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)


class UserProductListView(LoginRequiredMixin, generic.ListView):
    # list of products created by the request.user
    model = Product
    template_name = 'products.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)


class CreateCheckoutSession(generic.View):
    def post(self, request, *args, **kwargs):
        domain = 'https://example.com'
        if settings.DEBUG:
            domain = 'http://127.0.0.1:8000'

        product = Product.objects.get(slug=self.kwargs.get('slug'))

        user = request.user

        customer = None
        customer_email = None

        if request.user.is_authenticated:
            if request.user.stripe_customer_id:
                customer = user.stripe_customer_id
            else:
                customer_email = user.email

        product_image_urls = []

        if product.cover:
            product_image_urls.append(product.cover.url)
        else:
            product_image_urls.append('https://images.yourstory.com/cs/wordpress/2016/08/125-fall-in-love.png?fm=auto&ar=2:1&mode=crop&crop=face&w=600')

        session = stripe.checkout.Session.create(
            customer=customer,
            customer_email=customer_email,
            payment_method_types=['card'],
            payment_intent_data={
                'application_fee_amount': 1000,  # cents
                'transfer_data': {
                    'destination': product.user.stripe_account_id,
                }
            },
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.name,
                        'images': product_image_urls
                    },
                    'unit_amount': product.get_price_in_cents(),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=domain + reverse('checkout-success'),
            cancel_url=domain + reverse('discover'),
            metadata={
                'product_id': product.id,
            }
        )

        return JsonResponse({'id': session.id})


class CheckoutSuccessView(generic.TemplateView):
    template_name = 'checkout_success.html'


@csrf_exempt
def stripe_webhook(request, *args, **kwargs):
    SESSION_COMPLETED_EVENT = 'checkout.session.completed'
    ACCOUNT_UPDATED_EVENT = 'account.updated'

    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET_KEY
        )
    except ValueError as e:
        return HttpResponse(status=500)

    except SignatureVerificationError as e:
        return HttpResponse(status=500)

    if event.type == SESSION_COMPLETED_EVENT:
        product_id = event['data']['object']['metadata']['product_id']
        product = Product.objects.get(pk=product_id)

        stripe_customer_id = event['data']['object']['customer']
        try:
            user = User.objects.get(stripe_customer_id=stripe_customer_id)
            user.userlibrary.product.add(product)
        except ObjectDoesNotExist:
            stripe_customer_email = event['data']['object']['customer_details']['email']
            try:
                user = User.objects.get(email=stripe_customer_email)
                user.stripe_customer_id = stripe_customer_id
                user.save()
                user.userlibrary.product.add(product)
            except ObjectDoesNotExist:
                site_url = request.build_absolute_uri(reverse('account_signup'))
                PurchasedProduct.objects.create(email=stripe_customer_email, product=product)
                send_mail(
                    subject='Successful purchase',
                    message=f"You've just purchased the {product.name}. To access it you need to register. {site_url}",
                    recipient_list=[
                        stripe_customer_email
                    ],
                    from_email='test@test.com'
                )

    if event.type == ACCOUNT_UPDATED_EVENT:
        pass

    return HttpResponse()


