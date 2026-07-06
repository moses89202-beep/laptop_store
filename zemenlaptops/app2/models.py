import uuid
import os
from django.db import models
from myapp.models import Customer, Laptop

def receipt_upload_path(instance, filename):
    return os.path.join('receipts', f"{instance.tx_ref}_{filename}")

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    DELIVERY_METHOD_CHOICES = [
        ('delivery', 'Delivery'),
        ('pickup', 'In-Store Pickup'),
    ]
    LOGISTICS_STATUS_CHOICES = [
        ('pending', 'Pending/Preparing'),
        ('dispatched', 'Dispatched / Out for Delivery'),
        ('delivered', 'Delivered'),
        ('ready_for_pickup', 'Ready for Collection'),
        ('picked_up', 'Picked Up / Collected'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    tx_ref = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHOD_CHOICES, default='delivery')
    delivery_status = models.CharField(max_length=20, choices=LOGISTICS_STATUS_CHOICES, default='pending')
    receipt = models.FileField(
        upload_to=receipt_upload_path, 
        blank=True, 
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.customer.full_name or self.customer.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    laptop = models.ForeignKey(Laptop, on_delete=models.PROTECT) 
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) 

    def __str__(self):
        return f"{self.quantity} x {self.laptop.name}"