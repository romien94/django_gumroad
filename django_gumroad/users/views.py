from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


User = get_user_model()


class UserDetailView(LoginRequiredMixin, generic.DetailView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):

    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self):
        return self.request.user.get_absolute_url()  # type: ignore [union-attr]

    def get_object(self):
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, generic.RedirectView):

    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()


class UserLibraryView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'user_library.html'

    def get_context_data(self, **kwargs):
        context = super(UserLibraryView, self).get_context_data(**kwargs)
        stripe_account = stripe.Account.retrieve(self.request.user.stripe_account_id)
        context.update({
            'details_submitted': stripe_account['details_submitted']
        })
        return context


class StripeAccountLinkView(LoginRequiredMixin, generic.RedirectView):
    permanent = False

    def get_redirect_url(self):
        domain = 'https://example.com'
        if settings.DEBUG:
            domain = 'http://127.0.0.1:8000'
        account_links = stripe.AccountLink.create(
            account=self.request.user.stripe_account_id,
            refresh_url=domain + reverse('stripe-account-link'),
            return_url=domain + reverse('user-library'),
            type='account_onboarding',
        )
        return account_links['url']

