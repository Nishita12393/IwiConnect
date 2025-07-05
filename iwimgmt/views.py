from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from core.models import Iwi
from .forms import IwiForm, IwiArchiveForm

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def iwi_list(request):
    """List all iwis with filtering options"""
    show_archived = request.GET.get('show_archived', 'false').lower() == 'true'
    
    if show_archived:
        iwis = Iwi.objects.all().order_by('name')
    else:
        iwis = Iwi.objects.filter(is_archived=False).order_by('name')
    
    return render(request, 'iwimgmt/iwi_list.html', {
        'iwis': iwis,
        'show_archived': show_archived,
    })

@user_passes_test(is_admin)
def iwi_create(request):
    """Create a new iwi"""
    if request.method == 'POST':
        form = IwiForm(request.POST)
        if form.is_valid():
            iwi = form.save()
            messages.success(request, f'Iwi "{iwi.name}" created successfully.')
            return redirect('iwimgmt:iwi_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = IwiForm()
    
    return render(request, 'iwimgmt/iwi_form.html', {
        'form': form,
        'title': 'Create New Iwi',
        'submit_text': 'Create Iwi',
    })

@user_passes_test(is_admin)
def iwi_edit(request, iwi_id):
    """Edit an existing iwi"""
    iwi = get_object_or_404(Iwi, id=iwi_id)
    
    if request.method == 'POST':
        form = IwiForm(request.POST, instance=iwi)
        if form.is_valid():
            form.save()
            messages.success(request, f'Iwi "{iwi.name}" updated successfully.')
            return redirect('iwimgmt:iwi_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = IwiForm(instance=iwi)
    
    return render(request, 'iwimgmt/iwi_form.html', {
        'form': form,
        'iwi': iwi,
        'title': f'Edit Iwi: {iwi.name}',
        'submit_text': 'Update Iwi',
    })

@user_passes_test(is_admin)
def iwi_archive(request, iwi_id):
    """Archive an iwi"""
    iwi = get_object_or_404(Iwi, id=iwi_id, is_archived=False)
    
    if request.method == 'POST':
        form = IwiArchiveForm(request.POST)
        if form.is_valid():
            iwi.archive(archived_by=request.user)
            messages.success(request, f'Iwi "{iwi.name}" has been archived.')
            return redirect('iwimgmt:iwi_list')
    else:
        form = IwiArchiveForm()
    
    return render(request, 'iwimgmt/iwi_archive.html', {
        'iwi': iwi,
        'form': form,
    })

@user_passes_test(is_admin)
def iwi_unarchive(request, iwi_id):
    """Unarchive an iwi"""
    iwi = get_object_or_404(Iwi, id=iwi_id, is_archived=True)
    
    if request.method == 'POST':
        iwi.unarchive()
        messages.success(request, f'Iwi "{iwi.name}" has been unarchived.')
        return redirect('iwimgmt:iwi_list')
    
    return render(request, 'iwimgmt/iwi_unarchive.html', {
        'iwi': iwi,
    })

@user_passes_test(is_admin)
def iwi_detail(request, iwi_id):
    """View iwi details"""
    iwi = get_object_or_404(Iwi, id=iwi_id)
    
    return render(request, 'iwimgmt/iwi_detail.html', {
        'iwi': iwi,
    })
