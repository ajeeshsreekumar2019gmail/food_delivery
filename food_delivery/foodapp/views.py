from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from decimal import Decimal
from django.db.models import Count
from django.http import HttpResponseBadRequest
from .task import send_customer_welcome, send_restaurant_welcome, send_delivery_welcome,send_otp_email
from django.core.cache import cache
from django.utils.crypto import get_random_string

from .models import (
    CustomUser, Order, RestaurantProfile, FoodItem, Category,
    Cart, CartItem, OrderItem
)

from .forms import (
    Registerform, RestaurantProfileForm, FoodItemForm, CategoryForm,
    OrderForm, UserProfileForm, CustomPasswordChangeForm,
    CustomSetPasswordForm, CustomPasswordResetForm,DeliveryProfileForm
)
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


# ---------------- HOME ----------------
def home(request):
    """Homepage with real statistics"""
    context = {
        'restaurant_count': CustomUser.objects.filter(role='restaurant').count(),
        'customer_count': CustomUser.objects.filter(role='customer').count(),
        'delivery_count': CustomUser.objects.filter(role='delivery').count(),
        'order_count': Order.objects.count(),
    }
    return render(request, 'home.html', context)


# ---------------- DASHBOARD ----------------
@login_required(login_url='login')
def dashboard(request):
    user = request.user
    if user.is_superuser or user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'customer':
        return redirect('customer_dashboard')
    elif user.role == 'restaurant':
        return redirect('restaurant_dashboard')
    elif user.role == 'delivery':
        return redirect('delivery_dashboard')
    else:
        messages.error(request, "Unknown user role.")
        return redirect('home')


# ----------------  REGISTRATION ----------------
def register_customer(request):
    form = Registerform(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'customer'
        user.is_verified = True
        user.save()
        send_customer_welcome.delay(user.email, user.get_full_name() or user.username)
        login(request, user)
        messages.success(request, "Customer registered successfully.")
        return redirect('login')
    return render(request, 'customer_register.html', {'form': form})


def register_restaurant(request):
    form = Registerform(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'restaurant'
        user.is_verified = False
        user.save()
        send_restaurant_welcome.delay(user.email, user.get_full_name() or user.username)
        messages.success(request, "Restaurant registered successfully. Awaiting verification.")
        return redirect('login')
    return render(request, 'restaurant_register.html', {'form': form})


def register_delivery(request):
    form = Registerform(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'delivery'
        user.is_verified = False
        user.save()
        send_delivery_welcome.delay(user.email, user.get_full_name() or user.username)
        messages.success(request, "Delivery partner registered successfully. Awaiting verification.")
        return redirect('login')
    return render(request, 'delivery_register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, f"Login successful, {user.username}")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')


# ---------------- PASSWORDS ----------------
@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password changed successfully.")
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    return redirect('home')


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user =  CustomUser.objects.get(email=email)
            otp = get_random_string(6, "0123456789")
            
            
            cache.set(f"otp_{email}", otp, 300)
            send_otp_email.delay(email, otp)
            messages.success(request, "OTP sent to your email!")
            return redirect("verify_otp")
        except CustomUser.DoesNotExist:
            messages.error(request, "Email not found.")
    return render(request, "login.html")



def verify_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = request.POST.get("otp")
        new_password = request.POST.get("password")
        
        cached_otp = cache.get(f"otp_{email}")
        if cached_otp == otp:
            user = CustomUser.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            cache.delete(f"otp_{email}")  
            messages.success(request, "Password reset successfully!")
            return redirect("login")
        else:
            messages.error(request, "Invalid or expired OTP!")
            
    return render(request, "verify_otp.html")



@login_required
def reset_password(request):
    if request.method == 'POST':
        form = CustomSetPasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password reset successfully.")
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    return redirect('home')


# ---------------- ADMIN ----------------
@login_required(login_url='login')
def admin_dashboard(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    context = {
        'customers': CustomUser.objects.filter(role='customer').count(),
        'restaurants': CustomUser.objects.filter(role='restaurant').count(),
        'delivery_partners': CustomUser.objects.filter(role='delivery').count(),
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'pending_restaurants': CustomUser.objects.filter(role='restaurant', is_verified=False),
        'pending_delivery': CustomUser.objects.filter(role='delivery', is_verified=False),
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
def manage_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'manage_orders.html', {'orders': orders})



@login_required
def manage_restaurant(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')
    restaurants = CustomUser.objects.filter(role='restaurant')
    return render(request, 'manage_restaurants.html', {'restaurants': restaurants})


@login_required
def manage_delivery_partner(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')
    delivery_partners = CustomUser.objects.filter(role='delivery')
    return render(request, 'manage_delivery.html', {'delivery_partners': delivery_partners})


@login_required
def verify_user(request, user_id):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    user = get_object_or_404(CustomUser, id=user_id)
    user.is_verified = True
    user.save()
    messages.success(request, f"{user.username} verified successfully.")
    return redirect('admin_dashboard')


@login_required(login_url='login')
def manage_customers(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    customers = CustomUser.objects.filter(role='customer').order_by('-date_joined')
    return render(request, 'manage_customers.html', {'customers': customers})


@login_required(login_url='login')
def view_delivery_partner(request, partner_id):
    partner = get_object_or_404(CustomUser, id=partner_id, role='delivery')
    return render(request, 'delivery_partner_details.html', {'partner': partner})



@login_required(login_url='login')
def view_customer(request, customer_id):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    customer = get_object_or_404(CustomUser, id=customer_id, role='customer')
    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    return render(request, 'view_customer.html', {'customer': customer, 'orders': orders})


@login_required(login_url='login')
def view_restaurant(request, restaurant_id):
    restaurant_user = get_object_or_404(CustomUser, id=restaurant_id, role='restaurant')
    restaurant_profile = RestaurantProfile.objects.filter(user=restaurant_user).first()
    
    return render(request, 'restaurant_details.html', {
        'restaurant': restaurant_user,
        'profile': restaurant_profile,
    })


# ---------------- RESTAURANT ----------------
@login_required(login_url='login')
def restaurants_dashboard(request):
    if request.user.role != 'restaurant':
        messages.error(request, "You are not authorized to access the restaurant dashboard.")
        return redirect('dashboard')

    if not request.user.is_verified:
        messages.warning(request, "Your restaurant account is pending verification.")
        return redirect('home')

    restaurant_profile = getattr(request.user, 'restaurantprofile', None)
    if not restaurant_profile:
        messages.warning(request, "Please complete your restaurant profile first.")
        return redirect('restaurant_profile')

    context = {
        'restaurant_profile': restaurant_profile,
        'total_food_items': FoodItem.objects.filter(restaurant=restaurant_profile).count(),
        'total_orders': Order.objects.filter(restaurant=restaurant_profile).count(),
        'pending_orders': Order.objects.filter(restaurant=restaurant_profile, status='pending').count(),
    }
    return render(request, 'restaurant_dashboard.html', context)


@login_required(login_url='login')
def restaurant_profile(request):
    if request.user.role != 'restaurant':
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    try:
        restaurant = request.user.restaurantprofile
        is_update = True
    except RestaurantProfile.DoesNotExist:
        restaurant = None
        is_update = False

    if request.method == "POST":
        form = RestaurantProfileForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            restaurant_profile = form.save(commit=False)
            restaurant_profile.user = request.user
            restaurant_profile.save()
            messages.success(request, "Profile saved.")
            return redirect('restaurant_dashboard')
    else:
        form = RestaurantProfileForm(instance=restaurant)

    return render(request, 'restaurant_profile.html', {'form': form, 'is_update': is_update})


@login_required(login_url='login')
def add_category(request):
    if request.user.role != 'restaurant':
        messages.error(request, "Only restaurants can add categories.")
        return redirect('dashboard')

    try:
        restaurant = request.user.restaurantprofile
    except RestaurantProfile.DoesNotExist:
        messages.error(request, "Please add your restaurant details first.")
        return redirect('restaurant_profile')

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.restaurant = restaurant
            category.save()
            messages.success(request, f'Category "{category.name}" created.')
            return redirect('manage_menu')
    else:
        form = CategoryForm()

    return render(request, 'add_category.html', {'form': form})


@login_required(login_url='login')
def add_food_item(request):
    if request.user.role != 'restaurant':
        messages.error(request, "Only restaurants can add food items.")
        return redirect('dashboard')

    try:
        restaurant = request.user.restaurantprofile
    except RestaurantProfile.DoesNotExist:
        messages.error(request, "Please add your restaurant details first.")
        return redirect('restaurant_profile')

    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES, restaurant=restaurant)
        if form.is_valid():
            food_item = form.save(commit=False)
            food_item.restaurant = restaurant
            food_item.save()
            messages.success(request, f'"{food_item.name}" added to menu.')
            return redirect('manage_menu')
    else:
        form = FoodItemForm(restaurant=restaurant)
        form.fields['category'].queryset = Category.objects.filter(restaurant=restaurant)

    return render(request, 'add_food.html', {'form': form,'restaurant': restaurant })


@login_required(login_url='login')
def manage_menu(request):
    if request.user.role != 'restaurant':
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    try:
        restaurant = request.user.restaurantprofile
    except RestaurantProfile.DoesNotExist:
        messages.error(request, "Please add your restaurant details first.")
        return redirect('restaurant_profile')

    food_items = FoodItem.objects.filter(restaurant=restaurant)
    categories = Category.objects.filter(restaurant=restaurant)

    return render(request, 'manage_menu.html', {
        'food_items': food_items,
        'categories': categories,
        'restaurant': restaurant,
    })

@login_required(login_url='login')
def edit_food_item(request, food_id):
    if request.user.role != 'restaurant':
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')
   
    try:
        restaurant = request.user.restaurantprofile
    except RestaurantProfile.DoesNotExist:
        messages.error(request, "Please add your restaurant details first.")
        return redirect('restaurant_profile')

    try:
        food_item = FoodItem.objects.get(id=food_id, restaurant=restaurant)
    except FoodItem.DoesNotExist:
        messages.error(request, "Food item not found or you don't have permission to edit it.")
        return redirect('manage_menu')
    
    if request.method == 'POST':
        print("POST data:", request.POST)
        print("FILES:", request.FILES)
        
        form = FoodItemForm(
            request.POST,
            request.FILES,
            instance=food_item,
            restaurant=restaurant
        )
        
        if form.is_valid():
            updated_food_item = form.save()
            messages.success(request, f'"{updated_food_item.name}" updated successfully.')
            return redirect('manage_menu')
        else:
            print("Form errors:", form.errors.as_json())
            messages.error(request, "Please correct the errors below.")
    else:
        form = FoodItemForm(instance=food_item, restaurant=restaurant)

    return render(request, 'edit_food.html', {
        'form': form,
        'food_item': food_item
    })

@login_required(login_url='login')
def delete_food(request, food_id):
    if request.user.role != 'restaurant':
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    try:
        restaurant = request.user.restaurantprofile
    except RestaurantProfile.DoesNotExist:
        messages.error(request, "Please add your restaurant details first.")
        return redirect('restaurant_profile')

    food = get_object_or_404(FoodItem, id=food_id, restaurant=restaurant)

    if request.method == 'POST':
        food.delete()
        messages.success(request, f'"{food.name}" deleted.')
        return redirect('manage_menu')

    return render(request, 'delete_food.html', {'food_item': food})


@login_required(login_url='login')
def restaurant_orders(request):
    if request.user.role != 'restaurant':
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    try:
        restaurant = request.user.restaurantprofile
    except RestaurantProfile.DoesNotExist:
        messages.error(request, "Please add your restaurant details first.")
        return redirect('restaurant_profile')

    orders = Order.objects.filter(restaurant=restaurant).order_by('-created_at')
    return render(request, 'restaurant_orders.html', {'orders': orders})


# ---------------- CUSTOMER ----------------
@login_required(login_url='login')
def customer_dashboard(request):
    if request.user.role != 'customer':
        messages.error(request, "You are not authorized to access customer dashboard.")
        return redirect('dashboard')

    recent_orders = Order.objects.filter(customer=request.user).order_by('-created_at')[:5]
    
    
    cart_items_count = CartItem.objects.filter(
        cart__customer=request.user, 
        cart__is_active=True
    ).count()

    return render(request, 'customer_dashboard.html', {
        'recent_orders': recent_orders,
        'cart_items_count': cart_items_count,
    })
@login_required
def customer_profile(request):
    if request.user.role != 'customer':
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    form = UserProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('customer_profile')
    return render(request, 'customer_profile.html', {'form': form})


@login_required
def view_menu(request):
    if request.user.role != 'customer':
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    restaurants = RestaurantProfile.objects.filter(user__is_verified=True)
    food_items = FoodItem.objects.filter(is_available=True, restaurant__user__is_verified=True)

    return render(request, 'view_menu.html', {
        'food_items': food_items,
        'restaurants': restaurants,
    })


@login_required
def add_to_cart(request, food_id):
    if request.user.role != 'customer':
        return redirect('dashboard')

    food = get_object_or_404(FoodItem, id=food_id, is_available=True)

    cart, created = Cart.objects.get_or_create(customer=request.user, is_active=True)

    item, created = CartItem.objects.get_or_create(cart=cart, food_item=food)
    item.quantity = item.quantity + 1 if not created else 1
    item.save()

    return redirect('view_cart')



@login_required
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)

    action = request.POST.get('action')

    if action == 'increase':
        item.quantity += 1

    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
        else:
            item.delete()
            return redirect('view_cart')

    elif action == 'remove':
        item.delete()
        return redirect('view_cart')

    item.save()
    return redirect('view_cart')


@login_required
def view_cart(request):
    if request.user.role != 'customer':
        return redirect('dashboard')

    try:
        cart = Cart.objects.get(customer=request.user, is_active=True)
        items = CartItem.objects.filter(cart=cart)
        total = sum(i.quantity * i.food_item.price for i in items)
    except Cart.DoesNotExist:
        cart, items, total = None, [], 0

    return render(request, 'cart.html', {
        'cart': cart,
        'cart_items': items,
        'total_price': total
    })

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)
    item.delete()
    return redirect('view_cart')



# ---------------- CHECKOUT ----------------


@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(customer=request.user, is_active=True)
        items = CartItem.objects.filter(cart=cart)
    except Cart.DoesNotExist:
        return redirect('view_cart')

    if not items:
        return redirect('view_cart')

    total = sum(i.quantity * i.food_item.price for i in items)
    amount = int(total * 100)

    if request.method == 'POST':
        order = razorpay_client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': '0'
        })

    
        request.session['temp_order'] = {
            'cart_id': cart.id,
            'restaurant_id': items[0].food_item.restaurant.id,
            'total_price': float(total), 
            'razorpay_order_id': order['id'],  
            'order_id': order['id']
        }

        return redirect('payment')

    return render(request, 'checkout.html', {
        'cart_items': items,
        'total_price': total
    })

@login_required
def order_confirmation(request, order_id):
    if request.user.role != 'customer':
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    order = get_object_or_404(Order, id=order_id, customer=request.user)
    items = OrderItem.objects.filter(order=order).select_related('food')
    return render(request, 'order_confirmation.html', {'order': order, 'items': items})


@login_required
def customer_orders(request):
    if request.user.role != 'customer':
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'customer_orders.html', {'orders': orders})


# ---------------- DELIVERY ----------------

@login_required(login_url='login')
def delivery_profile_view(request):
    if request.method == 'POST':
        form = DeliveryProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('delivery_profile')
    else:
        form = DeliveryProfileForm(instance=request.user)
    
    return render(request, 'delivery_profile.html', {'form': form})



@login_required(login_url='login')
def delivery_dashboard(request):
    if request.user.role != 'delivery':
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    assigned_orders = Order.objects.filter(delivery_partner=request.user).order_by('-created_at')
    available_orders = Order.objects.filter(status='pending', delivery_partner__isnull=True).order_by('created_at')

    return render(request, 'delivery_dashboard.html', {
        'assigned_orders': assigned_orders,
        'available_orders': available_orders,
    })


@login_required
def accept_order(request, order_id):
    if request.user.role != 'delivery':
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    order = get_object_or_404(Order, id=order_id, status='pending', delivery_partner__isnull=True)

    if request.method == 'POST':
        order.delivery_partner = request.user
        order.status = 'delivering'
        order.save()
        messages.success(request, f"Order #{order.id} accepted.")
        return redirect('delivery_dashboard')

    return render(request, 'accept_order.html', {'order': order})


@login_required
def update_delivery_status(request, order_id):
    if request.user.role != 'delivery':
        messages.error(request, "You are not authorized.")
        return redirect('dashboard')

    order = get_object_or_404(Order, id=order_id, delivery_partner=request.user)

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Order.STATUS_CHOICES).keys():
            order.status = status
            order.save()
            messages.success(request, f"Order #{order.id} status updated.")
        else:
            messages.error(request, "Invalid status.")
        return redirect('delivery_dashboard')

    return render(request, 'update_delivery_status.html', {'order': order})


# ---------------- SEARCH ----------------
def food_search(request):
    query = request.GET.get('query', '')
    restaurant = request.GET.get('restaurant', '')
    max_price = request.GET.get('max_price', '')

    food_items = FoodItem.objects.filter(is_available=True)

    if query:
        food_items = food_items.filter(name__icontains=query)
    if restaurant:
        food_items = food_items.filter(restaurant__name__icontains=restaurant)
    if max_price:
        try:
            max_price_val = float(max_price)
            food_items = food_items.filter(price__lte=max_price_val)
        except ValueError:
            pass

    return render(request, 'food_search.html', {
        'query': query,
        'restaurant': restaurant,
        'max_price': max_price,
        'food_items': food_items
    })



# ---------------- payments ----------------



razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))


@login_required
def payment(request):
    temp = request.session.get('temp_order')
    if not temp:
        messages.error(request, "Session expired. Please checkout again.")
        return redirect('checkout')

    context = {
        'razorpay_order_id': temp['razorpay_order_id'],  #
        'razorpay_merchant_key': settings.RAZOR_KEY_ID,
        'razorpay_amount': int(temp['total_price'] * 100),  
        'currency': 'INR',
        'callback_url': 'paymenthandler/'
    }

    return render(request, 'payment.html', context)



@csrf_exempt
def paymenthandler(request):
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            
            if not all([payment_id, order_id, signature]):
                return render(request, "failed.html")

            params_dict = {
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature
            }

          
            razorpay_client.utility.verify_payment_signature(params_dict)

            temp = request.session.get('temp_order')
            if not temp:
                return render(request, "failed.html")

        
            amount = int(float(temp['total_price']) * 100)  
            razorpay_client.payment.capture(payment_id, amount)

            cart = Cart.objects.get(id=temp['cart_id'])
            cart_items = CartItem.objects.filter(cart=cart)

            order = Order.objects.create(
                customer=request.user,
                restaurant_id=temp['restaurant_id'],
                total_amount=temp['total_price'],  
                status='pending'
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    food=item.food_item,
                    quantity=item.quantity,
                    price=item.food_item.price  
                )

            cart.is_active = False
            cart.save()

            
            if 'temp_order' in request.session:
                del request.session['temp_order']

            return render(request, "success.html", {"order": order})

        except:
            
            return render(request, "failed.html")

    return HttpResponseBadRequest("Invalid Access")




