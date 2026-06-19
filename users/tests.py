from django.urls import reverse
from django.test import TestCase, Client

from users.models import User, Profile
from training.models import Service, Filiere
from users.forms import CustomUserCreationForm, CustomUserChangeForm


class ProfileModelTests(TestCase):
    def setUp(self):
        self.profile = Profile.objects.create(name="Manager")

    def test_profile_creation(self):
        self.assertEqual(self.profile.name, "Manager")

    def test_profile_str(self):
        self.assertEqual(str(self.profile), "Manager")

    def test_profile_unique_name(self):
        with self.assertRaises(Exception):
            Profile.objects.create(name="Manager")


class UserModelTests(TestCase):
    def setUp(self):
        self.profile = Profile.objects.create(name="Manager")
        self.service = Service.objects.create(nom="Service A")
        self.filiere = Filiere.objects.create(nom="Informatique", service=self.service)

    def test_user_creation(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="securepass123",
            profile=self.profile,
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("securepass123"))

    def test_user_with_filiere_and_service(self):
        user = User.objects.create_user(
            username="chef",
            email="chef@example.com",
            password="pass123",
            profile=self.profile,
            filiere=self.filiere,
            service=self.service,
        )
        self.assertEqual(user.filiere.nom, "Informatique")
        self.assertEqual(user.service.nom, "Service A")

    def test_user_str(self):
        user = User.objects.create_user(
            username="struser",
            email="str@example.com",
            password="pass123",
        )
        self.assertEqual(str(user), "struser")

    def test_user_defaults(self):
        user = User.objects.create_user(
            username="defaults",
            email="defaults@example.com",
            password="pass123",
        )
        self.assertIsNone(user.profile)
        self.assertIsNone(user.filiere)
        self.assertIsNone(user.service)

    def test_user_unique_username(self):
        User.objects.create_user(
            username="unique",
            email="u1@example.com",
            password="pass123",
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                username="unique",
                email="u2@example.com",
                password="pass123",
            )


class CustomUserCreationFormTests(TestCase):
    def setUp(self):
        self.profile = Profile.objects.create(name="Manager")

    def test_form_valid(self):
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'profile': self.profile.pk,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_valid_with_filiere_service(self):
        service = Service.objects.create(nom="Service A")
        filiere = Filiere.objects.create(nom="Informatique", service=service)
        form = CustomUserCreationForm(data={
            'username': 'chefuser',
            'email': 'chefuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': '',
            'last_name': '',
            'profile': self.profile.pk,
            'filiere': filiere.pk,
            'service': service.pk,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_password_mismatch(self):
        form = CustomUserCreationForm(data={
            'username': 'badpass',
            'email': 'badpass@example.com',
            'password1': 'Pass123!',
            'password2': 'DifferentPass!',
            'profile': self.profile.pk,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_form_invalid_empty_username(self):
        form = CustomUserCreationForm(data={
            'username': '',
            'email': 'empty@example.com',
            'password1': 'Pass123!',
            'password2': 'Pass123!',
            'profile': self.profile.pk,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)


class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="testpass123",
        )

    def test_login_get(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home/login.html")

    def test_login_post_success(self):
        response = self.client.post(reverse("login"), {
            "username": "loginuser",
            "password": "testpass123",
        })
        self.assertEqual(response.status_code, 302)
        # After successful login, should redirect to home '/'
        self.assertEqual(response.url, "/")

    def test_login_post_invalid(self):
        response = self.client.post(reverse("login"), {
            "username": "loginuser",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Identifiants invalides")

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))


class UserViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile = Profile.objects.create(name="Manager")
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )
        self.admin.profile = self.profile
        self.admin.is_staff = True
        self.admin.save()
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="regularpass123",
        )

    def test_user_list_requires_login(self):
        response = self.client.get(reverse("users"))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_user_list_as_logged_in(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("users"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "admin")

    def test_user_create_as_logged_in(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("user_create"), {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "profile": self.profile.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_user_detail_as_logged_in(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("user_detail", kwargs={"pk": self.regular_user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "regular")

    def test_user_update_as_logged_in(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("user_update", kwargs={"pk": self.regular_user.pk}),
            {
                "username": "updateduser",
                "email": "updated@example.com",
                "first_name": "Updated",
                "last_name": "User",
                "profile": self.profile.pk,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.username, "updateduser")
        self.assertEqual(self.regular_user.first_name, "Updated")

    def test_user_delete_as_logged_in(self):
        self.client.force_login(self.admin)
        temp_user = User.objects.create_user(
            username="tempuser",
            email="temp@example.com",
            password="temppass123",
        )
        response = self.client.post(reverse("user_delete", kwargs={"pk": temp_user.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=temp_user.pk).exists())

    def test_user_list_shows_stats(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("users"))
        self.assertEqual(response.status_code, 200)
        # Should show at least 2 users (admin + regular)
        self.assertContains(response, "admin")
        self.assertContains(response, "regular")