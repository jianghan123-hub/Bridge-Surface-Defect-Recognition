# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="用户名",
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': '请输入用户名'})
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': '请输入密码'})
    )
    remember_me = forms.BooleanField(
        label="记住我",
        required=False,
        widget=forms.CheckboxInput()
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label="电子邮箱",
        widget=forms.EmailInput(attrs={'class': 'input', 'placeholder': '请输入有效邮箱地址'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'input', 'placeholder': '请输入用户名(4-16位字符)'})
        self.fields['password1'].widget.attrs.update({'class': 'input', 'placeholder': '请输入密码(至少8位)'})
        self.fields['password2'].widget.attrs.update({'class': 'input', 'placeholder': '请再次输入密码'})