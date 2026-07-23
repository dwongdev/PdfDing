from admin import views as admin_views
from admin.forms import CreateUserForm, PasswordForm
from allauth.account.models import EmailAddress
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class TestLoginRequired(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='non_admin', password='password', email='a@a.com')
        self.user.save()
        self.client = Client()

        self.client.login(username='non_admin', password='password')

    def test_admin_required(self):
        response = self.client.get(reverse('user_overview'))

        self.assertEqual(response.status_code, 404)


class TestOverviewMixin(TestCase):
    def setUp(self):
        admin = User.objects.create_user(username='admin', password='password', email='a@a.com')
        admin.is_superuser = True
        admin.save()

        for i in range(1, 4):
            User.objects.create_user(username=f'user_{i}', password='12345', email=f'{i}_b@a.com')

    def test_filter_objects(self):
        for search_query, expected_result in zip(
            # also use some spaces in the admin search to verify this also works
            ['search=b@a.com', 'search=@a&tags=admin'],
            [['1_b@a.com', '2_b@a.com', '3_b@a.com'], ['a@a.com']],
        ):
            response = self.client.get(f'{reverse('user_overview')}?{search_query}')
            filtered_users = admin_views.OverviewMixin.filter_objects(response.wsgi_request)
            user_emails = [user.email for user in filtered_users]

            self.assertEqual(user_emails, expected_result)

    def test_get_extra_context(self):
        response = self.client.get(f'{reverse('user_overview')}?search=@a&tags=admin')

        generated_extra_context = admin_views.OverviewMixin.get_extra_context(response.wsgi_request)
        expected_extra_context = {'search_query': '@a', 'tag_query': ['admin'], 'page': 'user_overview'}

        self.assertEqual(generated_extra_context, expected_extra_context)

    def test_get_extra_context_empty_queries(self):
        response = self.client.get(reverse('user_overview'))

        generated_extra_context = admin_views.OverviewMixin.get_extra_context(response.wsgi_request)
        expected_extra_context = {'search_query': '', 'tag_query': [], 'page': 'user_overview'}

        self.assertEqual(generated_extra_context, expected_extra_context)


class TestAdminMixin(TestCase):
    def test_get_object(self):
        user = User.objects.create_user(username='non_admin', password='password', email='a@a.com')

        self.assertEqual(user, admin_views.AdminMixin.get_object(None, user.id))


class TestAdminViews(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password', email='a@a.com')
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()
        self.client = Client()

        self.client.login(username='admin', password='password')

    def test_remove_admin_rights(self):
        headers = {'HTTP_HX-Request': 'true'}
        self.client.post(reverse('admin_adjust_rights', kwargs={'identifier': self.user.id}), **headers)

        user = User.objects.get(id=self.user.id)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_add_admin_rights(self):
        user = User.objects.create_user(username='non_admin', password='12345', email='non_admin@a.com')

        headers = {'HTTP_HX-Request': 'true'}
        self.client.post(reverse('admin_adjust_rights', kwargs={'identifier': user.id}), **headers)

        user = User.objects.get(id=user.id)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_adjust_admin_rights_no_htmx(self):
        response = self.client.post(reverse('admin_adjust_rights', kwargs={'identifier': self.user.id}))
        self.assertRedirects(response, reverse('user_overview'), status_code=302)

    def test_get_information(self):
        for i in range(1, 4):
            User.objects.create_user(username=f'user_{i}', password='12345', email=f'{i}_b@a.com')

        response = self.client.get(reverse('instance_info'))

        self.assertEqual(response.context['number_of_users'], 4)
        self.assertEqual(response.context['number_of_pdfs'], 0)
        self.assertEqual(response.context['current_version'], 'DEV')

    def test_delete_get(self):
        user = User.objects.create_user(username='non_admin', password='12345', email='non_admin@a.com')

        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.get(reverse('admin_delete_user', kwargs={'identifier': user.id}), **headers)

        self.assertEqual(response.context['user_id'], str(user.id))
        self.assertEqual(response.context['user_mail'], user.email)
        self.assertTemplateUsed(response, 'partials/delete_user.html')

    def test_create_user_obj_save(self):
        email = 'a@b.com'
        assert not User.objects.filter(email=email).exists()
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))

        form = CreateUserForm(data={'email': email, 'password': 'pw', 'password2': 'pw'})
        form.is_valid()  # need to call is valid once to get access to cleaned data
        admin_views.CreateUser.obj_save(form, response.wsgi_request, None)

        generated_user = User.objects.get(email=email)
        assert generated_user.email == email
        email_address = EmailAddress.objects.get_primary(generated_user)
        assert email_address.verified

    def test_set_password_post(self):
        user = User.objects.create_user(username='some_user', password='password', email='b@a.com')
        response = self.client.post(
            reverse('admin_set_password', kwargs={'identifier': user.id}),
            data={
                'password': 'other_pw',
                'password2': 'other_pw',
            },
        )

        changed_user = User.objects.get(id=user.id)
        assert check_password('other_pw', changed_user.password)
        self.assertRedirects(response, reverse('user_overview'))

    def test_set_password_invalid_form(self):
        user = User.objects.create_user(username='some_user', password='password', email='b@a.com')
        response = self.client.post(
            reverse('admin_set_password', kwargs={'identifier': user.id}),
            data={'password': 'some_pw', 'password2': 'other_pw'},
        )

        self.assertIsInstance(response.context['form'], PasswordForm)
        self.assertTemplateUsed(response, 'admin_set_password.html')
