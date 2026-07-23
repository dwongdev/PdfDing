from admin.forms import CreateUserForm, PasswordForm
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.account.utils import setup_user_email
from base import base_views
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.db.models.functions import Lower
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render
from django.views import View
from django_htmx.http import HttpResponseClientRefresh
from pdf.models.pdf_models import Pdf


class BaseAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_superuser and self.request.user.is_staff:
            return True
        else:
            raise Http404("Given query not found...")


class BaseAdminMixin:
    obj_name = 'user'


class OverviewMixin(BaseAdminMixin):
    overview_page_name = 'user_overview_page'

    @staticmethod
    def get_sorting(request: HttpRequest):
        """Get the sorting of the overview page."""

        profile = request.user.profile

        sorting_dict = {
            'Newest': '-date_joined',
            'Oldest': 'date_joined',
            'Email_asc': Lower('email'),
            'Email_desc': Lower('email').desc(),
        }

        return sorting_dict[profile.user_sorting]

    @staticmethod
    def filter_objects(request: HttpRequest) -> QuerySet:
        """
        Filter the PDFs when performing a search in the overview.
        """

        users = User.objects.all()

        search = request.GET.get('search', '')
        tags = request.GET.get('tags', [])
        if tags:
            tags = tags.split(' ')

        if 'admin' in tags:
            users = users.filter(is_superuser=True)

        if search:
            users = users.filter(email__icontains=search)

        return users

    @staticmethod
    def get_extra_context(request: HttpRequest) -> dict:
        """get further information that needs to be passed to the template."""

        tag_query = request.GET.get('tags', [])
        if tag_query:
            tag_query = tag_query.split(' ')

        extra_context = {
            'search_query': request.GET.get('search', ''),
            'tag_query': tag_query,
            'page': 'user_overview',
        }

        return extra_context


class AdminMixin(BaseAdminMixin):
    @staticmethod
    def get_object(_, identifier: str):
        user = User.objects.get(id=identifier)

        return user


class Overview(BaseAdminRequiredMixin, OverviewMixin, base_views.BaseOverview):
    """
    View for the user overview page. This view performs the searching and sorting of the users. It's also responsible
    for paginating the users.
    """


class OverviewQuery(base_views.BaseOverviewQuery):
    """View for performing searches and sorting on the user overview page."""

    obj_name = 'user'


class DeleteProfile(BaseAdminRequiredMixin, AdminMixin, base_views.BaseDelete):
    """View for deleting a user profile"""

    def get(self, request: HttpRequest, identifier: str):
        """Triggered by htmx. Display an inline form for deleting the user."""

        if request.htmx:
            user = User.objects.get(id=identifier)

            return render(
                request,
                'partials/delete_user.html',
                {'user_id': identifier, 'user_mail': user.email},
            )

        return redirect('pdf_overview')  # pragma: no cover


class CreateUser(BaseAdminRequiredMixin, base_views.BaseAdd):
    """View for adjusting the admin rights"""

    template_name = 'admin_create_user.html'
    obj_name = 'user'
    form = CreateUserForm

    def get_context_get(self, __, ___):  # pragma: no cover
        """Get the context needed to be passed to the template containing the form for creating a workspace."""

        context = {'form': self.form(), 'page': 'admin_create_user'}

        return context

    @classmethod
    def obj_save(cls, form: CreateUserForm, request: HttpRequest, __):
        email = form.cleaned_data.get("email")
        adapter = get_adapter()
        user = adapter.new_user(request)
        adapter.save_user(request, user, form)
        setup_user_email(request, user, [EmailAddress(email=email)])
        email_address = EmailAddress.objects.get_primary(user)
        email_address.verified = True
        email_address.save()


class AdjustAdminRights(BaseAdminRequiredMixin, View):
    """View for adjusting the admin rights."""

    def post(self, request: HttpRequest, identifier: str):
        if request.htmx:
            user = User.objects.get(id=identifier)

            if user.is_staff and user.is_superuser:
                user.is_staff = False
                user.is_superuser = False
            else:
                user.is_staff = True
                user.is_superuser = True

            user.save()

            return HttpResponseClientRefresh()

        return redirect('user_overview')


class ResetMfa(BaseAdminRequiredMixin, View):
    """View for resseting 2FA of a user."""

    def post(self, request: HttpRequest, identifier: str):
        if request.htmx:
            user = User.objects.get(id=identifier)

            if user.profile.mfa_activated:
                user.authenticator_set.all().delete()
                user.save()

            return HttpResponseClientRefresh()

        return redirect('user_overview')


class SetPassword(BaseAdminRequiredMixin, View):
    """View for resseting the password of a user."""

    def get(self, request: HttpRequest, identifier: str):  # pragma: no cover
        user = User.objects.get(id=identifier)
        context = {'form': PasswordForm(), 'user': user, 'page': 'admin_create_user'}

        return render(request, 'admin_set_password.html', context)

    def post(self, request: HttpRequest, identifier: str):

        form = PasswordForm(request.POST)
        user = User.objects.get(id=identifier)
        # follow=True is needed for getting the message
        context = {'form': form, 'user': user, 'page': 'admin_set_password'}

        if form.is_valid():
            if not user.profile.uses_social:
                password = form.cleaned_data.get('password')
                user.password = make_password(password)
                user.save()

            return redirect('user_overview')

        return render(request, 'admin_set_password.html', context=context)


class Information(View):  # pragma: no cover
    """View for getting instance information"""

    def get(self, request: HttpRequest):
        """Get instance information"""

        number_of_users = User.objects.all().count()
        number_of_pdfs = Pdf.objects.all().count()

        context = {
            'number_of_users': number_of_users,
            'number_of_pdfs': number_of_pdfs,
            'current_version': settings.VERSION,
        }

        return render(request, 'information.html', context=context)
