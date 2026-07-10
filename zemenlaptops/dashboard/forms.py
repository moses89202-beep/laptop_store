from django import forms
from django.contrib.auth.models import User
from myapp.models import Laptop, Customer
from app2.models import Order, OrderItem

# --- Laptop Form ---
class LaptopForm(forms.ModelForm):
    class Meta:
        model = Laptop
        fields = [
            'name', 'brand', 'description', 'ram', 'cpu', 'gpu', 
            'os', 'storage', 'screen_size', 'image', 'quantity', 'price'
        ]

# --- User/Customer Forms ---
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {'password': forms.PasswordInput()}

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['full_name', 'email', 'address', 'phone_number']

from django import forms
from app2.models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['delivery_status', 'payment_status']