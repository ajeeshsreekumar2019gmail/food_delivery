from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings




@shared_task
def send_customer_welcome(email, name):
    send_mail(
        f'Welcome {name}!',
        f'Hi {name}, thanks for registering as a customer!',
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )
    return f"Sent welcome to customer: {email}"

@shared_task
def send_restaurant_welcome(email, name):
    send_mail(
        f'Welcome Restaurant {name}!',
        f'Hi {name}, thanks for registering your restaurant!',
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )
    return f"Sent welcome to restaurant: {email}"

@shared_task
def send_delivery_welcome(email, name):
    send_mail(
        f'Welcome Delivery Partner {name}!',
        f'Hi {name}, thanks for joining as delivery partner!',
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )
    return f"Sent welcome to delivery: {email}"


@shared_task
def send_otp_email(email, otp):
    send_mail(
        "Your OTP for Password Reset",
        f"Your OTP is: {otp}. It is valid for 5 minutes.",
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )
