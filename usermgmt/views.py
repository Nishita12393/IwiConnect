from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from core.models import CustomUser, Iwi, IwiLeader, Hapu, HapuLeader
from django.urls import reverse
from django.http import HttpResponseForbidden, FileResponse, Http404
from django.conf import settings
from core.views import send_account_approved_email, send_account_rejected_email
from django.core.paginator import Paginator
import os
import threading
import logging

logger = logging.getLogger(__name__)

def send_email_with_logging(email_function, user, email_type):
    """Send email with error logging"""
    try:
        email_function(user)
        logger.info(f"Successfully sent {email_type} email to user {user.email} (ID: {user.id})")
    except Exception as e:
        logger.error(f"Failed to send {email_type} email to user {user.email} (ID: {user.id}): {str(e)}")

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def user_list(request):
    state = request.GET.get('state', '')
    users = CustomUser.objects.all().order_by('-registered_at')
    if state:
        users = users.filter(state=state)
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        user_id = request.POST.get('verify_user_id')
        reject_id = request.POST.get('reject_user_id')
        if user_id:
            user_to_verify = get_object_or_404(CustomUser, id=user_id)
            user_to_verify.state = 'VERIFIED'
            user_to_verify.save()
            # Send approval email in background thread with error logging
            threading.Thread(
                target=send_email_with_logging, 
                args=(send_account_approved_email, user_to_verify, 'approval'), 
                daemon=True
            ).start()
            messages.success(request, f'User {user_to_verify.full_name} has been verified successfully.')
        elif reject_id:
            user_to_reject = get_object_or_404(CustomUser, id=reject_id)
            user_to_reject.state = 'REJECTED'
            user_to_reject.save()
            # Send rejection email in background thread with error logging
            threading.Thread(
                target=send_email_with_logging, 
                args=(send_account_rejected_email, user_to_reject, 'rejection'), 
                daemon=True
            ).start()
            messages.success(request, f'User {user_to_reject.full_name} has been rejected successfully.')
        return redirect(f"{reverse('usermgmt:user_list')}?state={state}")
    return render(request, 'usermgmt/user_list.html', {
        'page_obj': page_obj,
        'state': state,
        'states': CustomUser.STATE_CHOICES,
    })

@user_passes_test(is_admin)
def view_citizenship_document(request, user_id):
    user = CustomUser.objects.filter(id=user_id).first()
    if not user or not user.citizenship_document:
        raise Http404()
    file_path = user.citizenship_document.path
    if not os.path.exists(file_path):
        raise Http404()
    return FileResponse(open(file_path, 'rb'), as_attachment=False)

@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
def manage_iwi_leaders(request):
    iwis = Iwi.objects.filter(is_archived=False)
    selected_iwi_id = request.GET.get('iwi')
    selected_iwi = Iwi.objects.filter(id=selected_iwi_id, is_archived=False).first() if selected_iwi_id else None
    users = CustomUser.objects.filter(is_staff=False)
    if selected_iwi:
        users = users.filter(iwi=selected_iwi)
    leaders = IwiLeader.objects.filter(iwi=selected_iwi) if selected_iwi else []
    if request.method == 'POST' and selected_iwi:
        add_user_id = request.POST.get('add_leader')
        remove_user_id = request.POST.get('remove_leader')
        if add_user_id:
            user = CustomUser.objects.get(id=add_user_id)
            IwiLeader.objects.get_or_create(iwi=selected_iwi, user=user)
        if remove_user_id:
            IwiLeader.objects.filter(iwi=selected_iwi, user_id=remove_user_id).delete()
        return redirect(f'{request.path}?iwi={selected_iwi.id}')
    return render(request, 'usermgmt/manage_iwi_leaders.html', {
        'iwis': iwis,
        'users': users,
        'selected_iwi': selected_iwi,
        'leaders': leaders,
    })

@login_required
def manage_hapu_leaders(request):
    # Only Iwi leaders can access
    iwi_leaderships = IwiLeader.objects.filter(user=request.user)
    iwis = [il.iwi for il in iwi_leaderships]
    hapus = Hapu.objects.filter(iwi__in=iwis, is_archived=False)
    selected_hapu_id = request.GET.get('hapu')
    selected_hapu = Hapu.objects.filter(id=selected_hapu_id, iwi__in=iwis, is_archived=False).first() if selected_hapu_id else None
    
    # Initialize empty querysets
    users = CustomUser.objects.none()
    leaders = []
    
    if selected_hapu:
        # Get users who belong to the selected hapu and are not staff
        users = CustomUser.objects.filter(
            hapu=selected_hapu,
            is_staff=False,
            state='VERIFIED'  # Only show verified users
        ).exclude(
            hapu_leaderships__hapu=selected_hapu  # Exclude users who are already leaders
        ).order_by('full_name')
        
        # Get current leaders for this hapu
        leaders = HapuLeader.objects.filter(hapu=selected_hapu).select_related('user')
    
    if request.method == 'POST' and selected_hapu:
        add_user_id = request.POST.get('add_leader')
        remove_user_id = request.POST.get('remove_leader')
        if add_user_id:
            user = CustomUser.objects.get(id=add_user_id)
            HapuLeader.objects.get_or_create(hapu=selected_hapu, user=user)
        if remove_user_id:
            HapuLeader.objects.filter(hapu=selected_hapu, user_id=remove_user_id).delete()
        return redirect(f'{request.path}?hapu={selected_hapu.id}')
    
    return render(request, 'usermgmt/manage_hapu_leaders.html', {
        'hapus': hapus,
        'users': users,
        'selected_hapu': selected_hapu,
        'leaders': leaders,
    })

@login_required
def hapu_user_approval(request):
    """Allow hapu leaders to approve/reject users of their hapu"""
    # Check if user is a hapu leader
    hapu_leaderships = HapuLeader.objects.filter(user=request.user)
    if not hapu_leaderships.exists():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get the hapus this user leads
    user_hapus = [hl.hapu for hl in hapu_leaderships]
    
    # Get selected hapu (default to first hapu if none selected)
    selected_hapu_id = request.GET.get('hapu')
    if selected_hapu_id:
        selected_hapu = get_object_or_404(Hapu, id=selected_hapu_id, leaders__user=request.user)
    else:
        selected_hapu = user_hapus[0] if user_hapus else None
    
    if not selected_hapu:
        messages.error(request, 'No hapu found for your leadership.')
        return redirect('dashboard')
    
    # Get pending users for the selected hapu
    pending_users = CustomUser.objects.filter(
        hapu=selected_hapu,
        state='PENDING_VERIFICATION'
    ).order_by('-registered_at')
    
    # Pagination
    paginator = Paginator(pending_users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        user_id = request.POST.get('verify_user_id')
        reject_id = request.POST.get('reject_user_id')
        
        if user_id:
            user_to_verify = get_object_or_404(CustomUser, id=user_id, hapu=selected_hapu)
            user_to_verify.state = 'VERIFIED'
            user_to_verify.save()
            # Send approval email in background thread with error logging
            threading.Thread(
                target=send_email_with_logging, 
                args=(send_account_approved_email, user_to_verify, 'approval'), 
                daemon=True
            ).start()
            messages.success(request, f'User {user_to_verify.full_name} has been verified successfully.')
            
        elif reject_id:
            user_to_reject = get_object_or_404(CustomUser, id=reject_id, hapu=selected_hapu)
            user_to_reject.state = 'REJECTED'
            user_to_reject.save()
            # Send rejection email in background thread with error logging
            threading.Thread(
                target=send_email_with_logging, 
                args=(send_account_rejected_email, user_to_reject, 'rejection'), 
                daemon=True
            ).start()
            messages.success(request, f'User {user_to_reject.full_name} has been rejected successfully.')
        
        return redirect(f"{reverse('usermgmt:hapu_user_approval')}?hapu={selected_hapu.id}")
    
    return render(request, 'usermgmt/hapu_user_approval.html', {
        'page_obj': page_obj,
        'selected_hapu': selected_hapu,
        'user_hapus': user_hapus,
    })
