from django.shortcuts import render, redirect
from .forms import RegistrationForm, LoginForm
from django.contrib import messages
from django.http import JsonResponse
from core.models import Hapu, Iwi, CustomUser
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test, login_required

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.state = 'PENDING_VERIFICATION'
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Thank you for registering. Your account is pending admin verification.')
            return redirect('register')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def get_hapus(request):
    iwi_id = request.GET.get('iwi_id')
    hapus = Hapu.objects.filter(iwi_id=iwi_id).values('id', 'name')
    return JsonResponse(list(hapus), safe=False)

def get_hapus_htmx(request):
    iwi_id = request.GET.get('iwi_id') or request.GET.get('id_iwi')
    hapus = Hapu.objects.filter(iwi_id=iwi_id)
    return render(request, 'partials/hapu_options.html', {'hapus': hapus})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.state == 'VERIFIED':
                    login(request, user)
                    if user.is_staff:
                        return redirect('home')
                    else:
                        return redirect('user_dashboard')
                else:
                    form.add_error(None, 'Your account is not verified yet.')
            else:
                form.add_error(None, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_dashboard(request):
    total_iwis = Iwi.objects.count()
    total_hapus = Hapu.objects.count()
    total_users = CustomUser.objects.count()
    return render(request, 'core/admin_dashboard.html', {
        'total_iwis': total_iwis,
        'total_hapus': total_hapus,
        'total_users': total_users,
    })

@login_required
def user_dashboard(request):
    return render(request, 'core/user_dashboard.html', {'user': request.user})

# The template 'register.html' should be placed in 'core/templates/register.html'
