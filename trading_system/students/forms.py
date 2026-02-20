from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(
        choices=(
            ('TRADER', 'Trader'),
            ('MARKET_MAKER', 'Market Maker'),
        )
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
        role = self.cleaned_data.get('role')
        if role:
            from trading.models import BaseUser
            BaseUser.objects.update_or_create(
                username=user.username,
                defaults={'role': role},
            )
        return user


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()
from django import forms

class UserDeleteCSVForm(forms.Form):
    csv_file = forms.FileField()
