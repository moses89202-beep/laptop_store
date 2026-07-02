from django.db import models


class Laptop(models.Model):
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=100)
    description = models.TextField()
    ram = models.CharField(max_length=50)
    cpu = models.CharField(max_length=100)
    gpu = models.CharField(max_length=100, blank=True, null=True)
    os = models.CharField(null=True, blank=True)
    storage = models.CharField(max_length=100)
    screen_size = models.DecimalField(max_digits=4, decimal_places=1) 
    image = models.ImageField(upload_to='media/')
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10,  decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand} {self.name}"