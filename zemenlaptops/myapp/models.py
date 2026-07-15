from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Laptop(models.Model):
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=100)
    description = models.TextField()
    ram = models.CharField(max_length=50)
    cpu = models.CharField(max_length=100)
    gpu = models.CharField(max_length=100, blank=True, null=True)
    os = models.CharField(max_length=100, null=True, blank=True)
    storage = models.CharField(max_length=100)
    screen_size = models.DecimalField(max_digits=4, decimal_places=1)
    image = models.ImageField(upload_to='media/')
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand} {self.name}"

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum([r.rating for r in reviews]) / reviews.count(), 1)
        return 0


class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.full_name or self.user.username


class Review(models.Model):
    laptop = models.ForeignKey(
        Laptop,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('laptop', 'customer')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer} - {self.laptop} ({self.rating}⭐)"