from unittest import TestCase

import pytest
from admin import forms
from django.contrib.auth.models import User


class TestAdminForms(TestCase):
    @pytest.mark.django_db
    def test_clean_email(self):
        form = forms.CreateUserForm(data={'email': 'a@a.com', 'password': 'pw', 'password2': 'pw'})

        assert form.is_valid()
        assert 'a@a.com' == form.clean_email()

    @pytest.mark.django_db
    def test_clean_email_existing(self):
        self.user = User.objects.create_user(username='a@a.com', password='pw', email='a@a.com')

        form = forms.CreateUserForm(data={'email': 'a@a.com', 'password': 'pw', 'password2': 'pw'})

        assert not form.is_valid()
        assert form.errors['email'] == ['A user is already registered with this email address.']

    @pytest.mark.django_db
    def test_clean_password2(self):
        form = forms.CreateUserForm(data={'email': 'a@a.com', 'password': 'pw', 'password2': 'pw'})

        assert form.is_valid()
        assert 'pw' == form.clean_password2()

    @pytest.mark.django_db
    def test_clean_password2_not_matching_pws(self):
        form = forms.CreateUserForm(data={'email': 'a@a.com', 'password': 'pw', 'password2': 'different'})

        assert not form.is_valid()
        assert form.errors['password2'] == ['You must type the same password each time.']
