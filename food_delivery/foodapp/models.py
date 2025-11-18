from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    username = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=10,default='0000000000')
    address = models.TextField(max_length=100, blank=True, null=True)
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
        ('restaurant', 'Restaurant'),
        ('delivery', 'Delivery Partners'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.username

class RestaurantProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'restaurant'})
    name = models.CharField(max_length=255)
    address = models.TextField(max_length=100,blank=True)
    phone = models.CharField(max_length=15)
    image = models.ImageField(upload_to='restaurants/', blank=True, null=True)
    is_approved = models.BooleanField(default=False) 

    def __str__(self):
        return self.name

class Category(models.Model):
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name 

class FoodItem(models.Model):
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='food_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    preparation_time = models.PositiveIntegerField(default=15, help_text="Preparation time in minutes") 


    
    def __str__(self):
        return self.name



class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('available', 'Available for Delivery'),
        ('accepted', 'Accepted by Restaurant'),
        ('assigned', 'Assigned to Delivery'),
        ('delivering', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'customer'})
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE)
    delivery_partner = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='deliveries', limit_choices_to={'role': 'delivery'})
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    food = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) 

    def __str__(self):
        return f"{self.food.name} x {self.quantity}"

    

    

class Cart(models.Model):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
  

    def total_price(self):
        return self.quantity * self.food_item.price
    

