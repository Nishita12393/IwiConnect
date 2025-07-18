from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.core.paginator import Paginator
from django.db import models
from core.models import Hapu, Iwi
from .forms import HapuForm, HapuArchiveForm, HapuTransferForm

@login_required
def hapu_list(request):
    """List all hapus that the user can manage (iwi leader or hapu leader)"""
    # Get hapus from iwis where user is a leader OR hapus where user is a leader
    user_iwis = Iwi.objects.filter(leaders__user=request.user, is_archived=False)
    user_hapus = Hapu.objects.filter(leaders__user=request.user)
    hapus = Hapu.objects.filter(
        models.Q(iwi__in=user_iwis) | models.Q(pk__in=user_hapus.values_list('pk', flat=True))
    ).order_by('iwi__name', 'name')
    
    # Separate active and archived hapus
    active_hapus = hapus.filter(is_archived=False)
    archived_hapus = hapus.filter(is_archived=True)
    
    # Check for hapus with archived iwis
    hapus_with_archived_iwis = active_hapus.filter(iwi__is_archived=True)
    
    # Pagination for active hapus
    active_paginator = Paginator(active_hapus, 20)
    active_page_number = request.GET.get('active_page')
    active_page_obj = active_paginator.get_page(active_page_number)
    
    # Pagination for archived hapus
    archived_paginator = Paginator(archived_hapus, 20)
    archived_page_number = request.GET.get('archived_page')
    archived_page_obj = archived_paginator.get_page(archived_page_number)
    
    context = {
        'active_page_obj': active_page_obj,
        'archived_page_obj': archived_page_obj,
        'hapus_with_archived_iwis': hapus_with_archived_iwis,
    }
    return render(request, 'hapumgmt/hapu_list.html', context)

@login_required
def hapu_create(request):
    """Create a new hapu"""
    # Check if user is an iwi leader
    user_iwis = Iwi.objects.filter(leaders__user=request.user, is_archived=False)
    if not user_iwis.exists():
        messages.error(request, 'You must be an iwi leader to create hapus.')
        return redirect('hapumgmt:hapu_list')
    
    if request.method == 'POST':
        form = HapuForm(request.POST, user=request.user)
        if form.is_valid():
            hapu = form.save(commit=False)
            if form.iwi_field_visible:
                hapu.iwi = form.cleaned_data['iwi']
            else:
                hapu.iwi = form.iwi
            hapu.save()
            messages.success(request, f'Hapu "{hapu.name}" created successfully!')
            return redirect('hapumgmt:hapu_detail', pk=hapu.pk)
    else:
        form = HapuForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create New Hapu',
        'submit_text': 'Create Hapu'
    }
    return render(request, 'hapumgmt/hapu_form.html', context)

@login_required
def hapu_edit(request, pk):
    """Edit an existing hapu"""
    hapu = get_object_or_404(Hapu, pk=pk)
    
    # Check if user is a leader of the hapu's iwi OR a leader of this specific hapu
    if not (hapu.iwi.leaders.filter(user=request.user).exists() or hapu.leaders.filter(user=request.user).exists()):
        messages.error(request, 'You do not have permission to edit this hapu.')
        return redirect('hapumgmt:hapu_list')
    
    if request.method == 'POST':
        form = HapuForm(request.POST, instance=hapu, user=request.user)
        if form.is_valid():
            hapu = form.save(commit=False)
            if form.iwi_field_visible:
                hapu.iwi = form.cleaned_data['iwi']
            else:
                hapu.iwi = form.iwi
            hapu.save()
            messages.success(request, f'Hapu "{hapu.name}" updated successfully!')
            return redirect('hapumgmt:hapu_detail', pk=hapu.pk)
    else:
        form = HapuForm(instance=hapu, user=request.user)
    
    context = {
        'form': form,
        'hapu': hapu,
        'title': f'Edit Hapu: {hapu.name}',
        'submit_text': 'Update Hapu'
    }
    return render(request, 'hapumgmt/hapu_form.html', context)

@login_required
def hapu_detail(request, pk):
    """View hapu details"""
    hapu = get_object_or_404(Hapu, pk=pk)
    
    # Check if user is a leader of the hapu's iwi OR a leader of this specific hapu
    if not (hapu.iwi.leaders.filter(user=request.user).exists() or hapu.leaders.filter(user=request.user).exists()):
        messages.error(request, 'You do not have permission to view this hapu.')
        return redirect('hapumgmt:hapu_list')
    
    context = {
        'hapu': hapu,
    }
    return render(request, 'hapumgmt/hapu_detail.html', context)

@login_required
def hapu_archive(request, pk):
    """Archive a hapu"""
    hapu = get_object_or_404(Hapu, pk=pk)
    
    # Check if user is a leader of the hapu's iwi OR a leader of this specific hapu
    if not (hapu.iwi.leaders.filter(user=request.user).exists() or hapu.leaders.filter(user=request.user).exists()):
        messages.error(request, 'You do not have permission to archive this hapu.')
        return redirect('hapumgmt:hapu_list')
    
    if hapu.is_archived:
        messages.warning(request, 'This hapu is already archived.')
        return redirect('hapumgmt:hapu_detail', pk=hapu.pk)
    
    if request.method == 'POST':
        form = HapuArchiveForm(request.POST)
        if form.is_valid():
            hapu.archive(archived_by=request.user)
            messages.success(request, f'Hapu "{hapu.name}" has been archived.')
            return redirect('hapumgmt:hapu_list')
    else:
        form = HapuArchiveForm()
    
    context = {
        'hapu': hapu,
        'form': form,
    }
    return render(request, 'hapumgmt/hapu_archive.html', context)

@login_required
def hapu_unarchive(request, pk):
    """Unarchive a hapu"""
    hapu = get_object_or_404(Hapu, pk=pk)
    
    # Check if user is a leader of the hapu's iwi OR a leader of this specific hapu
    if not (hapu.iwi.leaders.filter(user=request.user).exists() or hapu.leaders.filter(user=request.user).exists()):
        messages.error(request, 'You do not have permission to unarchive this hapu.')
        return redirect('hapumgmt:hapu_list')
    
    if not hapu.is_archived:
        messages.warning(request, 'This hapu is not archived.')
        return redirect('hapumgmt:hapu_detail', pk=hapu.pk)
    
    if request.method == 'POST':
        hapu.unarchive()
        messages.success(request, f'Hapu "{hapu.name}" has been unarchived.')
        return redirect('hapumgmt:hapu_list')
    
    context = {
        'hapu': hapu,
    }
    return render(request, 'hapumgmt/hapu_unarchive.html', context)

@login_required
def hapu_transfer(request, pk):
    """Transfer a hapu to another iwi"""
    hapu = get_object_or_404(Hapu, pk=pk)
    
    # Check if user is a leader of the hapu's iwi OR a leader of this specific hapu
    if not (hapu.iwi.leaders.filter(user=request.user).exists() or hapu.leaders.filter(user=request.user).exists()):
        messages.error(request, 'You do not have permission to transfer this hapu.')
        return redirect('hapumgmt:hapu_list')
    
    # Only allow transfer if the current iwi is archived
    if not hapu.iwi.is_archived:
        messages.warning(request, 'You can only transfer hapus when their iwi is archived.')
        return redirect('hapumgmt:hapu_detail', pk=hapu.pk)
    
    # Check if there are any active iwis available for transfer
    available_iwis = Iwi.objects.filter(is_archived=False).exclude(pk=hapu.iwi.pk)
    if not available_iwis.exists():
        messages.error(request, 'No active iwis available for transfer.')
        return redirect('hapumgmt:hapu_detail', pk=hapu.pk)
    
    if request.method == 'POST':
        form = HapuTransferForm(request.POST, current_iwi=hapu.iwi)
        if form.is_valid():
            new_iwi = form.cleaned_data['new_iwi']
            old_iwi_name = hapu.iwi.name
            hapu.iwi = new_iwi
            hapu.save()
            messages.success(request, f'Hapu "{hapu.name}" has been transferred from "{old_iwi_name}" to "{new_iwi.name}".')
            return redirect('hapumgmt:hapu_detail', pk=hapu.pk)
    else:
        form = HapuTransferForm(current_iwi=hapu.iwi)
    
    context = {
        'hapu': hapu,
        'form': form,
    }
    return render(request, 'hapumgmt/hapu_transfer.html', context)
