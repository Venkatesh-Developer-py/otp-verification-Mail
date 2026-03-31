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

from urllib3 import request

def email_send(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        
        # Better email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return render(request, "email_send.html", {
                "error": "Please enter a valid email address"
            })
        
        otp = random.randint(100000, 999999)
        request.session.clear()  # Clean slate
        request.session['email'] = email
        request.session['otp'] = str(otp)
        request.session['otp_time'] = time.time()
        request.session['otp_attempts'] = 0
        
        # Ultra-modern email template
        send_modern_email(email, otp, "initial")
        print(f"Modern email sent to {email}")
        return redirect('verify')
    
    return render(request, "email_send.html")

def verify_otp(request):
    email = request.session.get('email')
    if not email:
        return redirect('email_send')
    
    # Expiry check
    if time.time() - request.session.get('otp_time', 0) > 120:
        request.session.clear()
        return render(request, "email_verification.html", {
            "expired": True, "email": email
        })
    
    if request.method == "POST":
        user_otp = request.POST.get("otp", "").strip()
        attempts = request.session.get('otp_attempts', 0) + 1
        
        if attempts > 5:
            request.session.clear()
            return render(request, "email_verification.html", {
                "error": "Too many attempts. Please restart.", "email": email
            })
        
        if user_otp == request.session.get("otp"):
            request.session.clear()
            return render(request, "success.html")
        
        request.session['otp_attempts'] = attempts
        return render(request, "email_verification.html", {
            "error": "Invalid code", 
            "email": email,
            "attempts_left": 5 - attempts
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
<!DOCTYPE html>
<html>
<body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8; padding:30px 0;">
<tr>
<td align="center">

<table width="480" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:8px; padding:30px;">

    <!-- Logo -->
    <tr>
        <td align="center" style="font-size:20px; font-weight:bold; color:#4f46e5;">
            📩 Apple Verification
        </td>
    </tr>

    <!-- Spacer -->
    <tr><td height="20"></td></tr>

    <!-- Title -->
    <tr>
        <td align="center" style="font-size:20px; font-weight:bold; color:#111827;">
            Verify Your Email
        </td>
    </tr>

    <!-- Subtitle -->
    <tr>
        <td align="center" style="font-size:14px; color:#6b7280; padding-top:10px;">
            Enter the verification code below to continue
        </td>
    </tr>

    <!-- Spacer -->
    <tr><td height="25"></td></tr>

    <!-- OTP -->
    <tr>
        <td align="center">
            <div style="display:inline-block; padding:15px 25px; font-size:28px; letter-spacing:6px; font-weight:bold; background:#f1f5f9; border-radius:6px; color:#111827;">
                {otp}
            </div>
        </td>
    </tr>

    <!-- Valid text -->
    <tr>
        <td align="center" style="font-size:13px; color:#ef4444; padding-top:15px;">
            This code will expire in 02 minutes
        </td>
    </tr>

    <!-- Spacer -->
    <tr><td height="25"></td></tr>

    <!-- Info -->
    <tr>
        <td align="center" style="font-size:13px; color:#374151; line-height:1.5;">
            If you didn’t request this, you can safely ignore this email.
        </td>
    </tr>

    <!-- Button -->
    <tr>
        <td align="center" style="padding-top:20px;">
            <a href="mailto:santhiyavenki0@gmail.com"
               style="background:#4f46e5; color:#ffffff; padding:10px 20px; text-decoration:none; border-radius:5px; font-size:13px;">
               Contact Support
            </a>
        </td>
    </tr>

    <!-- Footer -->
    <tr>
        <td align="center" style="font-size:12px; color:#9ca3af; padding-top:30px;">
            © 2026 Apple. All rights reserved.
        </td>
    </tr>

</table>

</td>
</tr>
</table>

</body>
</html>
"""

    text_content = f"""
Your verification code is: {otp}

This code will expire in 10 minutes.

If you did not request this, please ignore this email.
"""

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        print(f"Client-level email sent to {email}")
    except Exception as e:
        print(f"❌ Email failed: {e}")