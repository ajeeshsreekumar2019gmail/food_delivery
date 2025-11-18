from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, RestaurantProfile, FoodItem, Category



class Registerform(UserCreationForm):



    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']


class RestaurantProfileForm(forms.ModelForm):
    class Meta:
        model = RestaurantProfile
        fields = ['name', 'address', 'phone', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Appetizers, Main Course, Desserts'})
        }


class FoodItemForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = ['category', 'name', 'description', 'price', 'image', 'preparation_time', 'is_available']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe the food item...'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'preparation_time': forms.NumberInput(attrs={'min': '1', 'max': '120'}),
        }
    
    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)
        
        if restaurant:
            self.fields['category'].queryset = Category.objects.filter(restaurant=restaurant)

class FoodSearchForm(forms.Form):
    query = forms.CharField(
        max_length=100, 
        required=False, 
        widget=forms.TextInput(attrs={
            'placeholder': 'Search for food items...',
            'class': 'form-control'
        })
    )
    
    restaurant = forms.ModelChoiceField(
        queryset=RestaurantProfile.objects.filter(is_approved=True),
        required=False,
        empty_label="All Restaurants"
    )
    
    max_price = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Max price', 'step': '0.01'})
    )

class OrderForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea)
    special_instructions = forms.CharField(required=False, widget=forms.Textarea)


class OrderStatusForm(forms.Form):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = forms.ChoiceField(choices=STATUS_CHOICES)
    
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
   







class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

class CustomPasswordResetForm(forms.Form):
    email = forms.EmailField()

class CustomSetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)








class DeliveryProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'phone_number', 'address', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            }