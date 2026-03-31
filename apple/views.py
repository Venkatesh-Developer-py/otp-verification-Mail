import email
from django.shortcuts import render, redirect
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.http import JsonResponse
import random
import time
import json
from django.utils import timezone
import re


def email_send(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return render(request, "email_send.html", {
                "error": "Please enter a valid email address"
            })
        
        otp = random.randint(100000, 999999)
        request.session.clear()  
        request.session['email'] = email
        request.session['otp'] = str(otp)
        request.session['otp_time'] = time.time()
        request.session['otp_attempts'] = 0
        
        
        send_modern_email(email, otp, "initial")
        print(f"Modern email sent to {email}")
        return redirect('verify')
    
    return render(request, "email_send.html")

    
def verify_otp(request):
    email = request.session.get('email')
    if not email:
        return redirect('email_send')

    if time.time() - request.session.get('otp_time', 0) > 120:
        request.session.clear()
        return render(request, "email_verification.html", {
            "expired": True, "email": email
        })

    if request.method == "POST":
        user_otp = request.POST.get("otp", "").strip()
        attempts = request.session.get('otp_attempts', 0) + 1

        remaining_time = 120 - int(time.time() - request.session.get('otp_time', 0))
        if remaining_time < 0:
            remaining_time = 0

        if attempts > 5:
            request.session.clear()
            return render(request, "email_verification.html", {
                "error": "Too many attempts. Please restart.",
                "email": email,
                "remaining_time": remaining_time
            })

        if user_otp == request.session.get("otp"):
            request.session.clear()
            return render(request, "success.html")

        request.session['otp_attempts'] = attempts
        return render(request, "email_verification.html", {
            "error": "Invalid Otp..!Please try again..",
            "email": email,
            "attempts_left": 5 - attempts,
            "remaining_time": remaining_time
        })

    remaining_time = 120 - int(time.time() - request.session.get('otp_time', 0))
    if remaining_time < 0:
        remaining_time = 0

    return render(request, "email_verification.html", {
        "email": email,
        "remaining_time": remaining_time
    })

def resend_otp(request):
    email = request.session.get('email')
    if email:
        otp = random.randint(100000, 999999)
        request.session['otp'] = str(otp)
        request.session['otp_time'] = time.time()
        request.session['otp_attempts'] = 0
        send_modern_email(email, otp, "resend")
    return redirect('verify')
def send_modern_email(email, otp, type_="initial"):
    subject = f"Your Verification Code{' (Resent)' if type_=='resend' else ''}"
    from_email = f"Apple 📩 <{settings.EMAIL_HOST_USER}>"

    html_content = f"""
    <h2>Your OTP is: {otp}</h2>
    <p>This code expires in 2 minutes</p>
    """

    text_content = f"Your OTP is {otp}"

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        print("OTP sent")
    except Exception as e:
        print("EMAIL ERROR:", e)