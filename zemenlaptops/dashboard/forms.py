from django import forms
from django.contrib.auth.models import User
from myapp.models import Laptop, Customer
from app2.models import Order, OrderItem

class LaptopForm(forms.ModelForm):
    class Meta:
        model = Laptop
        fields = [
            'name', 'brand', 'description', 'ram', 'cpu', 'gpu', 
            'os', 'storage', 'screen_size', 'image', 'quantity', 'price'
        ]

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = User
        fields = ['username', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance or not self.instance.pk:
            self.fields['password'].required = True


class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['full_name', 'email', 'address', 'phone_number']


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'delivery_method', 
            'delivery_status', 
            'payment_status'
        ]