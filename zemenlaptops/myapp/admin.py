from django.contrib import admin
from .models import *

@admin.register(Laptop)
class LaptopAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'brand', 'ram', 'cpu', 'gpu', 'storage', 'screen_size', 'quantity', 'price', 'os'
    )
    list_filter = (
        'brand', 'ram', 'storage', 'screen_size',
    )
    ordering = ('brand', 'name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ("Basic Information", {
            'fields': ('name', 'brand', 'description', 'image')
        }),
        ("Specifications", {
            'fields': ('ram', 'cpu', 'gpu', 'storage', 'screen_size', 'os')
        }),
        ("Inventory & Pricing", {
            'fields': ('quantity', 'price')
        }),
        ("Timestamps", {
            'fields': ('created_at', 'updated_at')
        }),
    )

admin.site.register(Customer)