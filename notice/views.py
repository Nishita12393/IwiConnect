from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Notice, NoticeAcknowledgment
from .forms import NoticeForm
from core.models import Iwi, Hapu
from django.utils import timezone
from django.urls import reverse

def is_leader_or_admin(user):
    return user.is_authenticated and (user.is_staff or user.iwi_leaderships.exists() or user.hapu_leaderships.exists())

@login_required
def notice_list(request):
    notices = Notice.objects.filter(expiry_date__gt=timezone.now()).order_by('-priority', '-created_at')
    # Filtering
    audience = request.GET.get('audience')
    iwi = request.GET.get('iwi')
    hapu = request.GET.get('hapu')
    
    # Apply audience filter only if a specific audience is selected (not "All")
    if audience and audience != '':
        notices = notices.filter(audience=audience)
    
    # Apply iwi filter if selected
    if iwi:
        notices = notices.filter(iwi_id=iwi)
    
    # Apply hapu filter if selected
    if hapu:
        notices = notices.filter(hapu_id=hapu)
    
    # Pagination
    paginator = Paginator(notices, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    iwis = Iwi.objects.filter(is_archived=False)
    hapus = Hapu.objects.filter(is_archived=False)
    return render(request, 'notice/notice_list.html', {
        'page_obj': page_obj,
        'audience': audience,
        'iwi': iwi,
        'hapu': hapu,
        'iwis': iwis,
        'hapus': hapus,
    })

@login_required
def notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    # Track acknowledgment
    if not NoticeAcknowledgment.objects.filter(notice=notice, user=request.user).exists():
        NoticeAcknowledgment.objects.create(notice=notice, user=request.user)
    return render(request, 'notice/notice_detail.html', {'notice': notice})

@user_passes_test(is_leader_or_admin)
def create_notice(request):
    user = request.user
    is_admin = user.is_staff
    allowed_audience = [('ALL', 'All Users'), ('IWI', 'Specific Iwi'), ('HAPU', 'Specific Hapu')]
    iwi_qs = Iwi.objects.filter(is_archived=False)
    hapu_qs = Hapu.objects.filter(is_archived=False)
    if not is_admin:
        iwi_ids = list(user.iwi_leaderships.values_list('iwi_id', flat=True))
        hapu_ids = list(user.hapu_leaderships.values_list('hapu_id', flat=True))
        if iwi_ids:
            # Iwi leader (may also be hapu leader): can select from their iwi and its hapus
            iwi_qs = Iwi.objects.filter(id__in=iwi_ids, is_archived=False)
            hapu_qs = Hapu.objects.filter(iwi_id__in=iwi_ids, is_archived=False)
            allowed_audience = [('IWI', 'Specific Iwi'), ('HAPU', 'Specific Hapu')]
        elif hapu_ids:
            # Only hapu leader
            hapu_qs = Hapu.objects.filter(id__in=hapu_ids, is_archived=False)
            iwi_qs = Iwi.objects.filter(id__in=hapu_qs.values_list('iwi_id', flat=True), is_archived=False)
            allowed_audience = [('HAPU', 'Specific Hapu')]
    
    # Get hapu data with iwi information for JavaScript filtering
    hapu_data = []
    if hapu_qs.exists():
        hapu_data = list(hapu_qs.values('id', 'name', 'iwi_id').order_by('name'))
    
    # Get current datetime for minimum expiry date
    current_datetime = timezone.now().strftime('%Y-%m-%dT%H:%M')
    
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        form.fields['iwi'].queryset = iwi_qs
        form.fields['hapu'].queryset = hapu_qs
        form.fields['audience'].choices = allowed_audience
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = user
            notice.save()
            messages.success(request, 'Notice created successfully!')
            return redirect('notice:notice_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
            return redirect('notice:create_notice')
    else:
        form = NoticeForm()
        form.fields['iwi'].queryset = iwi_qs
        form.fields['hapu'].queryset = hapu_qs
        form.fields['audience'].choices = allowed_audience
    return render(request, 'notice/create_notice.html', {
        'form': form,
        'hapu_data': hapu_data,
        'min_datetime': current_datetime,
    })

@user_passes_test(is_leader_or_admin)
def manage_notices(request):
    notices = Notice.objects.all().order_by('-created_at')
    return render(request, 'notice/manage_notices.html', {'notices': notices})

@user_passes_test(is_leader_or_admin)
def edit_notice(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    user = request.user
    is_admin = user.is_staff
    allowed_audience = [('ALL', 'All Users'), ('IWI', 'Specific Iwi'), ('HAPU', 'Specific Hapu')]
    iwi_qs = Iwi.objects.filter(is_archived=False)
    hapu_qs = Hapu.objects.filter(is_archived=False)
    if not is_admin:
        iwi_ids = list(user.iwi_leaderships.values_list('iwi_id', flat=True))
        hapu_ids = list(user.hapu_leaderships.values_list('hapu_id', flat=True))
        if iwi_ids:
            iwi_qs = Iwi.objects.filter(id__in=iwi_ids, is_archived=False)
            hapu_qs = Hapu.objects.filter(iwi_id__in=iwi_ids, is_archived=False)
            allowed_audience = [('IWI', 'Specific Iwi'), ('HAPU', 'Specific Hapu')]
        elif hapu_ids:
            hapu_qs = Hapu.objects.filter(id__in=hapu_ids, is_archived=False)
            iwi_qs = Iwi.objects.filter(id__in=hapu_qs.values_list('iwi_id', flat=True), is_archived=False)
            allowed_audience = [('HAPU', 'Specific Hapu')]
    
    # Get hapu data with iwi information for JavaScript filtering
    hapu_data = []
    if hapu_qs.exists():
        hapu_data = list(hapu_qs.values('id', 'name', 'iwi_id').order_by('name'))
    
    # Get current datetime for minimum expiry date
    current_datetime = timezone.now().strftime('%Y-%m-%dT%H:%M')
    
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES, instance=notice)
        form.fields['iwi'].queryset = iwi_qs
        form.fields['hapu'].queryset = hapu_qs
        form.fields['audience'].choices = allowed_audience
        if form.is_valid():
            form.save()
            messages.success(request, 'Notice updated successfully!')
            return redirect('notice:manage_notices')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
            return redirect('notice:edit_notice', pk=notice.pk)
    else:
        form = NoticeForm(instance=notice)
        form.fields['iwi'].queryset = iwi_qs
        form.fields['hapu'].queryset = hapu_qs
        form.fields['audience'].choices = allowed_audience
    return render(request, 'notice/edit_notice.html', {
        'form': form, 
        'notice': notice,
        'hapu_data': hapu_data,
        'min_datetime': current_datetime,
    })

@user_passes_test(is_leader_or_admin)
def delete_notice(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        notice.delete()
        messages.success(request, 'Notice deleted successfully!')
        return redirect('notice:manage_notices')
    return render(request, 'notice/delete_notice.html', {'notice': notice})

@user_passes_test(is_leader_or_admin)
def expire_notice(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        notice.expiry_date = timezone.now()
        notice.save()
        messages.success(request, 'Notice expired successfully!')
        return redirect('notice:manage_notices')
    return render(request, 'notice/expire_notice.html', {'notice': notice})

@user_passes_test(is_leader_or_admin)
def notice_engagement(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    acknowledgments = notice.acknowledgments.select_related('user').all()
    return render(request, 'notice/notice_engagement.html', {'notice': notice, 'acknowledgments': acknowledgments})
