from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from core.models import CustomUser, Iwi, IwiLeader, Hapu, HapuLeader
from django.urls import reverse
from django.http import HttpResponseForbidden, FileResponse, Http404
from django.conf import settings
import os

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def user_list(request):
    state = request.GET.get('state', '')
    users = CustomUser.objects.all().order_by('-registered_at')
    if state:
        users = users.filter(state=state)
    if request.method == 'POST':
        user_id = request.POST.get('verify_user_id')
        reject_id = request.POST.get('reject_user_id')
        if user_id:
            user_to_verify = get_object_or_404(CustomUser, id=user_id)
            user_to_verify.state = 'VERIFIED'
            user_to_verify.save()
        elif reject_id:
            user_to_reject = get_object_or_404(CustomUser, id=reject_id)
            user_to_reject.state = 'REJECTED'
            user_to_reject.save()
        return redirect(f"{reverse('user_list')}?state={state}")
    return render(request, 'usermgmt/user_list.html', {
        'users': users,
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
    iwis = Iwi.objects.all()
    selected_iwi_id = request.GET.get('iwi')
    selected_iwi = Iwi.objects.filter(id=selected_iwi_id).first() if selected_iwi_id else None
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
    hapus = Hapu.objects.filter(iwi__in=iwis)
    users = CustomUser.objects.filter(is_staff=False)
    selected_hapu_id = request.GET.get('hapu')
    selected_hapu = Hapu.objects.filter(id=selected_hapu_id, iwi__in=iwis).first() if selected_hapu_id else None
    if selected_hapu:
        users = users.filter(hapu=selected_hapu)
    leaders = HapuLeader.objects.filter(hapu=selected_hapu) if selected_hapu else []
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
