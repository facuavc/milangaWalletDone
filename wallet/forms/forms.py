from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from wallet.models import Gasto, Ingreso, Recordatorio, forgotPassword

#Se definen los formularios personalizados con sus respectivas validacione

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name','last_name','password1', 'password2']

LoginForm = AuthenticationForm

ChangePassForm = PasswordChangeForm

class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = '__all__'
    
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }
        
class IngresoForm(forms.ModelForm):
    class Meta:
        model=Ingreso
        fields='__all__'
    
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }

class recordatoriosForm(forms.ModelForm):
    class Meta:
        model=Recordatorio
        fields='__all__'
    
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }

class forgotPasswordForm(forms.ModelForm):
    class Meta:
        model=forgotPassword
        fields='__all__'
    
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }

