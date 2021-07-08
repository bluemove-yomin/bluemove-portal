from allauth.socialaccount.forms import SignupForm
from django import forms

# models
from .models import *


class BluemoveSocialSignupForm(SignupForm):
    last_name = forms.CharField(
        max_length=10,
        label="성",
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "성을 입력하세요.",
            }
        ),
    )
    first_name = forms.CharField(
        max_length=10,
        label="이름",
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "이름을 입력하세요.",
            }
        ),
    )
    email = forms.CharField(
        max_length=40,
        label="이메일 주소",
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "class": "form-control",
                "placeholder": "이메일 주소를 입력하세요.",
                "readOnly": "",
            }
        ),
    )
    phone = forms.CharField(
        max_length=13,
        min_length=13,
        label="휴대전화 번호",
        widget=forms.TextInput(
            attrs={
                "type": "tel",
                "class": "form-control",
                "placeholder": "휴대전화 번호를 입력하세요.",
                "onkeypress": "onlyNumbers(event)",
            }
        ),
    )

    def save(self, request):
        user = super(BluemoveSocialSignupForm, self).save(request)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()
        profile = Profile()
        profile.user = user
        profile.phone = self.cleaned_data["phone"]
        profile.save()
        return user
