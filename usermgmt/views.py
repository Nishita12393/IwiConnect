from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from core.models import CustomUser
from django.urls import reverse
from django.http import HttpResponseForbidden, FileResponse, Http404
from django.conf import settings
import os

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def user_list(request):
    state = request.GET.get('state', '')
    users = CustomUser.objects.all()
    if state:
        users = users.filter(state=state)
    if request.method == 'POST':
        user_id = request.POST.get('verify_user_id')
        user_to_verify = get_object_or_404(CustomUser, id=user_id)
        user_to_verify.state = 'VERIFIED'
        user_to_verify.save()
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
