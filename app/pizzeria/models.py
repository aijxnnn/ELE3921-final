from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin

class MenuItem(models.Model):
    ITEM_CATEGORY = [
        ('pizza', 'Pizza'),
        ('drink', 'Drink'),
        ('topping', 'Topping'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=10, choices=ITEM_CATEGORY)
    description = models.TextField(blank=True)
    image_filename = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

class MenuItemSize(models.Model):
    SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('0.33l', '0.33 L'),
        ('0.5l', '0.5 L'),
        ('1.5l', '1.5 L'),
    ]
    item = models.ForeignKey('MenuItem', on_delete=models.CASCADE, related_name='item_variant')
    size = models.CharField(max_length=20, choices=SIZE_CHOICES)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = ('item', 'size')

    def __str__(self):
        return f"{self.item.name} - {self.size}"
    
class PizzaTopping(models.Model):
    pizza = models.ForeignKey(MenuItem, on_delete=models.CASCADE, limit_choices_to={'category': 'pizza'}, related_name='pizza')
    topping = models.ForeignKey(MenuItem, on_delete=models.CASCADE, limit_choices_to={'category': 'topping'}, related_name='topping')

    def __str__(self):
        return f"{self.pizza.name}"
    
class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('complete', 'Complete'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    total_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"Order #{self.pk} - {self.user.username}"

class OrderItem(models.Model):
    order             = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    item_name         = models.CharField(max_length=200,blank=True)
    item_size         = models.CharField(max_length=20, blank=True)
    extra_toppings    = models.TextField(blank=True)
    removed_toppings  = models.TextField(blank=True)
    total_item_price  = models.DecimalField(max_digits=7, decimal_places=2, blank=True)
