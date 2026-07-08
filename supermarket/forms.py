from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class SignUpForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        label='Full Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': ' ',
            'autocomplete': 'name',
        }),
    )
    username = forms.CharField(
        max_length=150,
        label='Username',
        widget=forms.TextInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': ' ',
            'autocomplete': 'username',
        }),
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': ' ',
            'autocomplete': 'email',
        }),
    )
    phone = forms.CharField(
        max_length=20,
        label='Phone Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': ' ',
            'autocomplete': 'tel',
        }),
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control auth-input auth-password-input',
            'placeholder': ' ',
            'autocomplete': 'new-password',
        }),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control auth-input auth-password-input',
            'placeholder': ' ',
            'autocomplete': 'new-password',
        }),
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')

        if password1:
            try:
                validate_password(password1, user=User(
                    username=cleaned_data.get('username', ''),
                    email=cleaned_data.get('email', ''),
                    first_name=cleaned_data.get('full_name', ''),
                ))
            except ValidationError as exc:
                self.add_error('password1', exc)

        return cleaned_data
