from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Home and authentication
    path('homepage', home, name='home'),  
    path('dashboard/', dashboard, name='dashboard'),
    
    # Authentication
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),

    # Registration
    path('register/customer/', register_customer, name='register_customer'),
    path('register/restaurant/', register_restaurant, name='register_restaurant'),
    path('register/delivery/', register_delivery, name='register_delivery'),

    # Password management
    path('password/change/', change_password, name='change_password'),
    path('password/forgot/', forgot_password, name='forgot_password'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('password/reset/', reset_password, name='reset_password'),

    # Admin routes
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/orders/', manage_orders, name='manage_orders'),
    path('admin/manage-restaurants/', manage_restaurant, name='manage_restaurants'),
    path('admin/manage-delivery/', manage_delivery_partner, name='manage_delivery_partners'),
    path('admin/manage-customers/', manage_customers, name='manage_customers'),
    
    path('admin/delivery-partners/<int:partner_id>/', view_delivery_partner, name='view_delivery_partner'),
   path('view-restaurant/<int:restaurant_id>/', view_restaurant, name='view_restaurant'),
    path('admin/view-customer/<int:customer_id>/', view_customer, name='view_customer'),
    path('admin/verify-user/<int:user_id>/', verify_user, name='verify_user'),

    # Restaurant routes
    path('restaurant/dashboard/', restaurants_dashboard, name='restaurant_dashboard'),
    path('restaurant/profile/', restaurant_profile, name='restaurant_profile'),
    path('restaurant/category/add/', add_category, name='add_category'),  
    path('restaurant/food/add/', add_food_item, name='add_food_item'),
    path('restaurant/food/edit/<int:food_id>/', edit_food_item, name='edit_food_item'),
    path('restaurant/food/delete/<int:food_id>/', delete_food, name='delete_food_item'),
    path('restaurant/manage-menu/', manage_menu, name='manage_menu'),
    path('restaurant/orders/', restaurant_orders, name='restaurant_orders'),


    # Customer routes
    path('customer/dashboard/', customer_dashboard, name='customer_dashboard'),
    path('customer/profile/', customer_profile, name='customer_profile'),

    # Menu and cart
    path('menu/', view_menu, name='view_menu'),
    path('cart/', view_cart, name='view_cart'),
    path('cart/add/<int:food_id>/', add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),

    # Orders
    path('checkout/', checkout, name='checkout'),
    path('order/confirmation/<int:order_id>/', order_confirmation, name='order_confirmation'),
    path('orders/', customer_orders, name='customer_orders'),

    # Delivery
    path('delivery/', delivery_profile_view, name='delivery_profile'),
    path('delivery/dashboard/', delivery_dashboard, name='delivery_dashboard'),
    path('delivery/accept-order/<int:order_id>/', accept_order, name='accept_order'),
    path('delivery/update-status/<int:order_id>/', update_delivery_status, name='update_delivery_status'),

    # Search
    path('food/search/', food_search, name='food_search'),
    path('payment/', payment, name='payment'),
    path('paymenthandler/', paymenthandler, name='paymenthandler'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  
