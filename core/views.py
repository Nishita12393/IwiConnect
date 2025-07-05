from django.shortcuts import render, redirect
from .forms import RegistrationForm, LoginForm, PasswordResetRequestForm, SetPasswordForm
from django.contrib import messages
from django.http import JsonResponse
from core.models import Hapu, Iwi, CustomUser
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.forms import PasswordChangeForm
from core.helpers import get_app_name, get_logo_url, get_from_email
from django import forms
from django.core.mail import send_mail
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.template.loader import render_to_string
from django.conf import settings
import threading
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

def send_email_with_logging(email_function, *args, email_type):
    """Send email with error logging"""
    try:
        email_function(*args)
        # Extract user from args for logging
        user = args[0] if args else None
        if user and hasattr(user, 'email') and hasattr(user, 'id'):
            logger.info(f"Successfully sent {email_type} email to user {user.email} (ID: {user.id})")
        else:
            logger.info(f"Successfully sent {email_type} email")
    except Exception as e:
        # Extract user from args for logging
        user = args[0] if args else None
        if user and hasattr(user, 'email') and hasattr(user, 'id'):
            logger.error(f"Failed to send {email_type} email to user {user.email} (ID: {user.id}): {str(e)}")
        else:
            logger.error(f"Failed to send {email_type} email: {str(e)}")

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.state = 'PENDING_VERIFICATION'
            user.set_password(form.cleaned_data['password'])
            user.save()
            # Send welcome email in a background thread with error logging
            threading.Thread(
                target=send_email_with_logging, 
                args=(send_welcome_email, user, 'welcome'), 
                daemon=True
            ).start()
            messages.success(request, 'Thank you for registering. Your account is pending admin verification.')
            return redirect('register')
        else:
            # If form is invalid, redirect back to the form with error message
            messages.error(request, 'Please correct the errors below and try again.')
            return redirect('register')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def get_hapus(request):
    iwi_id = request.GET.get('iwi_id')
    hapus = Hapu.objects.filter(iwi_id=iwi_id, is_archived=False).values('id', 'name')
    return JsonResponse(list(hapus), safe=False)

def get_hapus_htmx(request):
    iwi_id = request.GET.get('iwi_id') or request.GET.get('id_iwi')
    hapus = Hapu.objects.filter(iwi_id=iwi_id, is_archived=False)
    return render(request, 'partials/hapu_options.html', {'hapus': hapus})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.state == 'VERIFIED':
                    login(request, user)
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Your account is not verified yet.')
                    return redirect('login')
            else:
                messages.error(request, 'Invalid email or password.')
                return redirect('login')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def is_admin(user):
    return user.is_authenticated and user.is_staff

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user = request.user
    # Admin
    if user.is_staff:
        total_iwis = Iwi.objects.filter(is_archived=False).count()
        total_hapus = Hapu.objects.count()
        total_users = CustomUser.objects.count()
        return render(request, 'core/admin_dashboard.html', {
            'total_iwis': total_iwis,
            'total_hapus': total_hapus,
            'total_users': total_users,
            'user': user,
        })
    # Iwi or Hapu Leader
    iwi_leaderships = user.iwi_leaderships.all()
    hapu_leaderships = user.hapu_leaderships.all()
    return render(request, 'core/user_dashboard.html', {
        'user': user,
        'iwi_leaderships': iwi_leaderships,
        'hapu_leaderships': hapu_leaderships,
    })

def home(request):
    return render(request, 'core/landing.html', {'user': request.user})

def app_name_context_processor(request):
    return {'app_name': get_app_name()}

class EmailChangeForm(forms.Form):
    new_email = forms.EmailField(label='New Email', max_length=254, widget=forms.EmailInput(attrs={'class': 'form-control', 'required': True}))
    password = forms.CharField(label='Current Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'required': True}))

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_new_email(self):
        email = self.cleaned_data['new_email']
        if CustomUser.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        if password and not self.user.check_password(password):
            self.add_error('password', 'Incorrect password.')
        return cleaned_data

@login_required
def profile(request):
    user = request.user
    password_form = PasswordChangeForm(user)
    email_form = EmailChangeForm(user)
    password_success = False
    email_success = False
    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was updated successfully!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the password errors below.')
                return redirect('profile')
        elif 'change_email' in request.POST:
            email_form = EmailChangeForm(user, request.POST)
            if email_form.is_valid():
                user.email = email_form.cleaned_data['new_email']
                user.save()
                messages.success(request, 'Your email was updated successfully!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the email errors below.')
                return redirect('profile')
    return render(request, 'core/profile.html', {
        'user': user,
        'password_form': password_form,
        'email_form': email_form,
        'password_success': password_success,
        'email_success': email_success,
    })

def send_welcome_email(user):
    """Send welcome email to new user"""
    try:
        from django.template.loader import render_to_string
        from django.conf import settings
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from core.helpers import get_logo_url, get_from_email, get_app_name
        
        subject = 'Welcome to IwiConnect'
        plain_message = (
            'Kia ora {},\n\n'
            'Thank you for registering with IwiConnect! Your account is pending admin verification.\n\n'
            'Naku noa,\nIwiConnect Team'
        ).format(user.full_name)
        html_message = render_to_string('email/welcome_email.html', {
            'name': user.full_name,
            'logo_url': get_logo_url(),
        })
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = get_app_name() + ' <' + get_from_email() + '>'
        msg['To'] = user.email
        part1 = MIMEText(plain_message, 'plain')
        part2 = MIMEText(html_message, 'html')
        msg.attach(part1)
        msg.attach(part2)
        smtp_host = settings.EMAIL_HOST
        smtp_port = settings.EMAIL_PORT
        smtp_user = settings.EMAIL_HOST_USER
        smtp_password = settings.EMAIL_HOST_PASSWORD
        use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
        ssl_context = getattr(settings, 'EMAIL_SSL_CONTEXT', None)
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            if use_tls:
                server.starttls(context=ssl_context)
            server.login(smtp_user, smtp_password)
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        logger.info(f"Successfully sent welcome email to user {user.email} (ID: {user.id})")
    except Exception as e:
        logger.error(f"Failed to send welcome email to user {user.email} (ID: {user.id}): {str(e)}")
        raise

def send_account_approved_email(user):
    """Send email notification when user account is approved"""
    try:
        from django.template.loader import render_to_string
        from django.conf import settings
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from core.helpers import get_logo_url, get_from_email, get_app_name
        
        subject = 'Account Approved - IwiConnect'
        plain_message = (
            'Kia ora {},\n\n'
            'Great news! Your IwiConnect account has been approved.\n\n'
            'You can now log in to your account and start using all the features of IwiConnect.\n\n'
            'Naku noa,\nIwiConnect Team'
        ).format(user.full_name)
        
        html_message = render_to_string('email/account_approved.html', {
            'name': user.full_name,
            'logo_url': get_logo_url(),
        })
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = get_app_name() + ' <' + get_from_email() + '>'
        msg['To'] = user.email
        part1 = MIMEText(plain_message, 'plain')
        part2 = MIMEText(html_message, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        smtp_host = settings.EMAIL_HOST
        smtp_port = settings.EMAIL_PORT
        smtp_user = settings.EMAIL_HOST_USER
        smtp_password = settings.EMAIL_HOST_PASSWORD
        use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
        ssl_context = getattr(settings, 'EMAIL_SSL_CONTEXT', None)
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            if use_tls:
                server.starttls(context=ssl_context)
            server.login(smtp_user, smtp_password)
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        logger.info(f"Successfully sent account approval email to user {user.email} (ID: {user.id})")
    except Exception as e:
        logger.error(f"Failed to send account approval email to user {user.email} (ID: {user.id}): {str(e)}")
        raise

def send_account_rejected_email(user):
    """Send email notification when user account is rejected"""
    try:
        from django.template.loader import render_to_string
        from django.conf import settings
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from core.helpers import get_logo_url, get_from_email, get_app_name
        
        subject = 'Account Application Status - IwiConnect'
        plain_message = (
            'Kia ora {},\n\n'
            'We regret to inform you that your IwiConnect account application has been rejected.\n\n'
            'This may be due to incomplete information or issues with the provided documentation. '
            'If you believe this is an error, please contact us for further assistance.\n\n'
            'Naku noa,\nIwiConnect Team'
        ).format(user.full_name)
        
        html_message = render_to_string('email/account_rejected.html', {
            'name': user.full_name,
            'logo_url': get_logo_url(),
        })
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = get_app_name() + ' <' + get_from_email() + '>'
        msg['To'] = user.email
        part1 = MIMEText(plain_message, 'plain')
        part2 = MIMEText(html_message, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        smtp_host = settings.EMAIL_HOST
        smtp_port = settings.EMAIL_PORT
        smtp_user = settings.EMAIL_HOST_USER
        smtp_password = settings.EMAIL_HOST_PASSWORD
        use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
        ssl_context = getattr(settings, 'EMAIL_SSL_CONTEXT', None)
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            if use_tls:
                server.starttls(context=ssl_context)
            server.login(smtp_user, smtp_password)
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        logger.info(f"Successfully sent account rejection email to user {user.email} (ID: {user.id})")
    except Exception as e:
        logger.error(f"Failed to send account rejection email to user {user.email} (ID: {user.id}): {str(e)}")
        raise

def generate_reset_token():
    """Generate a secure random token for password reset"""
    return secrets.token_urlsafe(32)

def send_password_reset_email(user, reset_token, request=None):
    """Send password reset email to user"""
    try:
        from django.template.loader import render_to_string
        from django.conf import settings
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from core.helpers import get_logo_url, get_from_email, get_app_name
        
        subject = 'Password Reset Request - IwiConnect'
        
        # Build reset URL - if request is not available, use a placeholder
        if request:
            reset_url = f"{request.build_absolute_uri('/')[:-1]}/reset-password/{reset_token}/"
        else:
            # Fallback for background thread
            reset_url = f"http://localhost:8000/reset-password/{reset_token}/"
        
        plain_message = (
            'Kia ora {},\n\n'
            'You requested a password reset for your IwiConnect account.\n\n'
            'Click the following link to reset your password:\n{}\n\n'
            'This link will expire in 24 hours.\n\n'
            'If you did not request this reset, please ignore this email.\n\n'
            'Naku noa,\nIwiConnect Team'
        ).format(user.full_name, reset_url)
        
        html_message = render_to_string('email/password_reset_email.html', {
            'name': user.full_name,
            'reset_url': reset_url,
            'logo_url': get_logo_url(),
        })
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = get_app_name() + ' <' + get_from_email() + '>'
        msg['To'] = user.email
        part1 = MIMEText(plain_message, 'plain')
        part2 = MIMEText(html_message, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        smtp_host = settings.EMAIL_HOST
        smtp_port = settings.EMAIL_PORT
        smtp_user = settings.EMAIL_HOST_USER
        smtp_password = settings.EMAIL_HOST_PASSWORD
        use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
        ssl_context = getattr(settings, 'EMAIL_SSL_CONTEXT', None)
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            if use_tls:
                server.starttls(context=ssl_context)
            server.login(smtp_user, smtp_password)
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        logger.info(f"Successfully sent password reset email to user {user.email} (ID: {user.id})")
    except Exception as e:
        logger.error(f"Failed to send password reset email to user {user.email} (ID: {user.id}): {str(e)}")
        raise

def password_reset_request(request):
    """Handle password reset request"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email, state='VERIFIED')
                # Generate reset token and store it in session for demo purposes
                # In production, you'd want to store this in the database with an expiration
                reset_token = generate_reset_token()
                request.session['reset_token'] = reset_token
                request.session['reset_email'] = email
                request.session['reset_expires'] = (timezone.now() + timedelta(hours=24)).isoformat()
                
                # Send email in background thread with error logging
                threading.Thread(
                    target=send_email_with_logging, 
                    args=(send_password_reset_email, user, reset_token, request, 'password_reset'), 
                    daemon=True
                ).start()
                
                messages.success(request, 'Password reset instructions have been sent to your email address.')
                return redirect('login')
            except CustomUser.DoesNotExist:
                # Don't reveal if email exists or not for security
                messages.success(request, 'If an account with that email exists, password reset instructions have been sent.')
                return redirect('login')
        else:
            # If form is invalid, redirect back to the form with error message
            messages.error(request, 'Please enter a valid email address.')
            return redirect('password_reset_request')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'password_reset_request.html', {'form': form})

def password_reset_confirm(request, token):
    """Handle password reset confirmation"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Check if token is valid and not expired
    stored_token = request.session.get('reset_token')
    stored_email = request.session.get('reset_email')
    stored_expires = request.session.get('reset_expires')
    
    if not all([stored_token, stored_email, stored_expires]):
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('login')
    
    try:
        expires = datetime.fromisoformat(stored_expires)
        if timezone.now() > expires:
            messages.error(request, 'Password reset link has expired.')
            # Clear session data
            for key in ['reset_token', 'reset_email', 'reset_expires']:
                request.session.pop(key, None)
            return redirect('login')
    except ValueError:
        messages.error(request, 'Invalid password reset link.')
        return redirect('login')
    
    if token != stored_token:
        messages.error(request, 'Invalid password reset link.')
        return redirect('login')
    
    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = CustomUser.objects.get(email=stored_email, state='VERIFIED')
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                
                # Clear session data
                for key in ['reset_token', 'reset_email', 'reset_expires']:
                    request.session.pop(key, None)
                
                messages.success(request, 'Your password has been reset successfully. You can now login with your new password.')
                return redirect('login')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User account not found.')
                return redirect('login')
        else:
            # If form is invalid, redirect back to the form with error message
            messages.error(request, 'Please check your password and try again.')
            return redirect('password_reset_confirm', token=token)
    else:
        form = SetPasswordForm()
    
    return render(request, 'password_reset_confirm.html', {'form': form})

# The template 'register.html' should be placed in 'core/templates/register.html'
