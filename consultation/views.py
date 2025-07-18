from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from .forms import ProposalForm
from .models import Proposal, VotingOption, Vote, ProposalComment, Iwi, Hapu
from core.models import CustomUser
from functools import wraps
from django.core.paginator import Paginator

def is_leader(user, iwi_id=None, hapu_id=None):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    if iwi_id and user.iwi_leaderships.filter(iwi_id=iwi_id).exists():
        return True
    if hapu_id and user.hapu_leaderships.filter(hapu_id=hapu_id).exists():
        return True
    return False

def leader_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        iwi_id = request.GET.get('iwi') or request.POST.get('iwi')
        hapu_id = request.GET.get('hapu') or request.POST.get('hapu')
        if not is_leader(request.user, iwi_id=iwi_id, hapu_id=hapu_id):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('You do not have permission to access this page.')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def create_proposal(request):
    initial = {}
    user = request.user
    is_admin = user.is_staff
    # Pre-select Iwi or Hapu for leaders
    iwi_id = request.GET.get('iwi')
    hapu_id = request.GET.get('hapu')
    if iwi_id:
        initial['iwi'] = iwi_id
    if hapu_id:
        initial['hapu'] = hapu_id
    # Set allowed consultation types and queryset restrictions
    allowed_types = [('PUBLIC', 'Public'), ('IWI', 'Restricted to Iwi'), ('HAPU', 'Restricted to Hapu')]
    iwi_qs = Iwi.objects.filter(is_archived=False)
    hapu_qs = Hapu.objects.filter(is_archived=False)
    if not is_admin:
        iwi_ids = list(user.iwi_leaderships.values_list('iwi_id', flat=True))
        hapu_ids = list(user.hapu_leaderships.values_list('hapu_id', flat=True))
        # Only include non-archived iwis
        active_iwis = list(Iwi.objects.filter(id__in=iwi_ids, is_archived=False))
        active_hapus = list(Hapu.objects.filter(id__in=hapu_ids, is_archived=False))
        if active_iwis:
            iwi_qs = Iwi.objects.filter(id__in=[iwi.id for iwi in active_iwis], is_archived=False)
        else:
            iwi_qs = Iwi.objects.none()
        if active_hapus:
            hapu_qs = Hapu.objects.filter(id__in=[hapu.id for hapu in active_hapus], is_archived=False)
        else:
            hapu_qs = Hapu.objects.none()
        # Determine allowed_types
        if active_iwis and len(iwi_ids) == 1 and Iwi.objects.filter(id=iwi_ids[0], is_archived=True).exists():
            # Only one iwi, and it is archived: do not allow IWI
            allowed_types = [('HAPU', 'Restricted to Hapu')] if active_hapus else []
        elif active_iwis and active_hapus:
            allowed_types = [('IWI', 'Restricted to Iwi'), ('HAPU', 'Restricted to Hapu')]
        elif active_iwis:
            allowed_types = [('IWI', 'Restricted to Iwi')]
        elif active_hapus:
            allowed_types = [('HAPU', 'Restricted to Hapu')]
        else:
            allowed_types = []
    
    if request.method == 'POST':
        form = ProposalForm(request.POST)
        form.fields['iwi'].queryset = iwi_qs
        form.fields['hapu'].queryset = hapu_qs
        form.fields['consultation_type'].choices = allowed_types
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.created_by = request.user
            proposal.save()
            # Save voting options
            options = [opt.strip() for opt in form.cleaned_data['voting_options'].splitlines() if opt.strip()]
            for opt in options:
                VotingOption.objects.create(proposal=proposal, text=opt)
            form.save_m2m()
            messages.success(request, 'Consultation created successfully!')
            return redirect('consultation:proposal_detail', pk=proposal.pk)
        else:
            messages.error(request, 'Please correct the errors below and try again.')
            # Use the same querysets as the initial form setup
            form.fields['iwi'].queryset = iwi_qs
            form.fields['hapu'].queryset = hapu_qs
            form.fields['consultation_type'].choices = allowed_types
            return render(request, 'consultation/create_proposal.html', {'form': form})
    else:
        form = ProposalForm(initial=initial)
        form.fields['iwi'].queryset = iwi_qs
        form.fields['hapu'].queryset = hapu_qs
        form.fields['consultation_type'].choices = allowed_types
        # Restrict Iwi/Hapu choices for leaders
        if iwi_id:
            form.fields['iwi'].queryset = Iwi.objects.filter(id=iwi_id)
            form.fields['hapu'].queryset = Hapu.objects.filter(iwi_id=iwi_id, is_archived=False)
        if hapu_id:
            hapu = Hapu.objects.filter(id=hapu_id, is_archived=False).first()
            if hapu:
                form.fields['iwi'].initial = hapu.iwi.id
                form.fields['iwi'].queryset = Iwi.objects.filter(id=hapu.iwi.id)
                form.fields['iwi'].disabled = True
            form.fields['hapu'].queryset = Hapu.objects.filter(id=hapu_id, is_archived=False)
    return render(request, 'consultation/create_proposal.html', {'form': form})

@user_passes_test(is_leader)
def proposal_list(request):
    proposals = Proposal.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(proposals, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'consultation/proposal_list.html', {'page_obj': page_obj})

@user_passes_test(is_leader)
def proposal_detail(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    return render(request, 'consultation/proposal_detail.html', {'proposal': proposal})

@login_required
def active_consultations(request):
    now = timezone.now()
    user = request.user
    
    # Base queryset for active, upcoming, and past consultations
    base_qs = Proposal.objects.filter(is_draft=False)
    active_qs = base_qs.filter(start_date__lte=now, end_date__gte=now)
    upcoming_qs = base_qs.filter(start_date__gt=now)
    past_qs = base_qs.filter(end_date__lt=now)
    
    # Filter consultations based on user access
    if user.is_staff:
        # Admin sees all consultations
        proposals_qs = active_qs.order_by('-created_at')
        upcoming_proposals_qs = upcoming_qs.order_by('start_date')  # Order by start date for upcoming
        past_proposals_qs = past_qs.order_by('-created_at')
    else:
        # Regular users see consultations based on their access level
        user_iwi = user.iwi
        # Get all hapus where the user is a leader
        leader_hapus = list(user.hapu_leaderships.values_list('hapu_id', flat=True))
        # Also include user's main hapu if set
        if user.hapu and user.hapu.id not in leader_hapus:
            leader_hapus.append(user.hapu.id)
        
        active_filters = Q(consultation_type='PUBLIC')
        upcoming_filters = Q(consultation_type='PUBLIC')
        past_filters = Q(consultation_type='PUBLIC')
        
        # Add IWI-specific consultations if user belongs to the iwi
        if user_iwi:
            active_filters |= Q(consultation_type='IWI', iwi=user_iwi)
            upcoming_filters |= Q(consultation_type='IWI', iwi=user_iwi)
            past_filters |= Q(consultation_type='IWI', iwi=user_iwi)
        
        # Add HAPU-specific consultations if user is a leader of the hapu
        if leader_hapus:
            active_filters |= Q(consultation_type='HAPU', hapu_id__in=leader_hapus)
            upcoming_filters |= Q(consultation_type='HAPU', hapu_id__in=leader_hapus)
            past_filters |= Q(consultation_type='HAPU', hapu_id__in=leader_hapus)
        
        # Apply filters and order
        proposals_qs = active_qs.filter(active_filters).order_by('-created_at')
        upcoming_proposals_qs = upcoming_qs.filter(upcoming_filters).order_by('start_date')  # Order by start date for upcoming
        past_proposals_qs = past_qs.filter(past_filters).order_by('-created_at')
    
    # Pagination
    active_page_number = request.GET.get('active_page')
    past_page_number = request.GET.get('past_page')
    active_paginator = Paginator(proposals_qs, 6)
    past_paginator = Paginator(past_proposals_qs, 6)
    proposals = active_paginator.get_page(active_page_number)
    past_proposals = past_paginator.get_page(past_page_number)
    
    # Get top 5 upcoming consultations (no pagination needed)
    upcoming_proposals = upcoming_proposals_qs[:5]
    
    return render(request, 'consultation/active_consultations.html', {
        'proposals': proposals,
        'past_proposals': past_proposals,
        'upcoming_proposals': upcoming_proposals,
    })

@login_required
def member_consultation_detail(request, pk):
    user = request.user
    
    # Get the proposal and check access
    proposal = get_object_or_404(Proposal, pk=pk, is_draft=False)
    
    # Check if consultation is past or future
    now = timezone.now()
    is_past = proposal.end_date < now
    is_future = proposal.start_date > now
    
    # Check if user has access to this consultation
    if not user.is_staff:
        # Regular users can only access consultations they're supposed to see
        user_iwi = user.iwi
        # Get all hapus where the user is a leader
        leader_hapus = list(user.hapu_leaderships.values_list('hapu_id', flat=True))
        if user.hapu and user.hapu.id not in leader_hapus:
            leader_hapus.append(user.hapu.id)
        
        # Check if user has access based on consultation type
        has_access = False
        
        if proposal.consultation_type == 'PUBLIC':
            has_access = True
        elif proposal.consultation_type == 'IWI' and user_iwi and proposal.iwi == user_iwi:
            has_access = True
        elif proposal.consultation_type == 'HAPU' and proposal.hapu and proposal.hapu.id in leader_hapus:
            has_access = True
        
        if not has_access:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('You do not have permission to access this consultation.')
    
    user_vote = Vote.objects.filter(proposal=proposal, user=request.user).first()
    voted = user_vote is not None
    comment_added = False
    
    # Disallow voting if consultation is in the future
    if request.method == 'POST' and is_future:
        messages.error(request, 'Voting is not allowed until the consultation starts.')
        return redirect('consultation:member_consultation_detail', pk=proposal.pk)
    
    if request.method == 'POST' and not is_past and not is_future:
        user_vote = Vote.objects.filter(proposal=proposal, user=request.user).first()
        voted = user_vote is not None
        if voted:
            messages.error(request, 'You have already voted in this consultation.')
        else:
            option_id = request.POST.get('voting_option')
            option = VotingOption.objects.filter(pk=option_id, proposal=proposal).first()
            if option:
                try:
                    vote = Vote.objects.create(
                        proposal=proposal,
                        user=request.user,  # Always save user
                        voting_option=option
                    )
                    voted = True
                    user_vote = vote
                    messages.success(request, 'Your vote has been recorded')
                except Exception:
                    messages.error(request, 'A voting error occurred. Please try again.')
            if proposal.enable_comments and request.POST.get('comment'):
                ProposalComment.objects.create(
                    proposal=proposal,
                    user=None if proposal.anonymous_feedback else request.user,
                    text=request.POST.get('comment')
                )
                comment_added = True
        # Redirect after POST to prevent form resubmission
        return redirect('consultation:member_consultation_detail', pk=proposal.pk)
    elif request.method == 'POST' and is_past:
        messages.error(request, 'This consultation has ended. Voting is no longer allowed.')
        return redirect('consultation:member_consultation_detail', pk=proposal.pk)
    
    comments = proposal.comments.all() if proposal.enable_comments else []
    return render(request, 'consultation/member_consultation_detail.html', {
        'proposal': proposal,
        'voted': voted,
        'user_vote': user_vote,
        'comments': comments,
        'comment_added': comment_added,
        'is_past': is_past,
        'is_future': is_future,
    })

@login_required
def consultation_result(request, pk):
    user = request.user
    
    # Get the proposal and check access
    proposal = get_object_or_404(Proposal, pk=pk, is_draft=False)
    
    # Check if user has access to this consultation
    if not user.is_staff:
        # Regular users can only access consultations they're supposed to see
        user_iwi = user.iwi
        user_hapu = user.hapu
        
        # Check if user has access based on consultation type
        has_access = False
        
        if proposal.consultation_type == 'PUBLIC':
            has_access = True
        elif proposal.consultation_type == 'IWI' and user_iwi and proposal.iwi == user_iwi:
            has_access = True
        elif proposal.consultation_type == 'HAPU' and user_hapu and proposal.hapu == user_hapu:
            has_access = True
        
        if not has_access:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('You do not have permission to access this consultation.')
    now = timezone.now()
    if proposal.end_date > now:
        return redirect('consultation:member_consultation_detail', pk=pk)
    # Calculate vote counts and percentages
    options = proposal.voting_options.all()
    total_votes = proposal.votes.count()
    results = []
    for option in options:
        count = proposal.votes.filter(voting_option=option).count()
        percent = (count / total_votes * 100) if total_votes > 0 else 0
        results.append({'option': option.text, 'count': count, 'percent': percent})
    comments = proposal.comments.all() if proposal.enable_comments else []
    return render(request, 'consultation/consultation_result.html', {
        'proposal': proposal,
        'results': results,
        'total_votes': total_votes,
        'comments': comments,
    })

@user_passes_test(is_leader)
def moderate_comments(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    comments = proposal.comments.all()
    if request.method == 'POST':
        for comment in comments:
            if f'approve_{comment.id}' in request.POST:
                comment.is_approved = True
                comment.save()
            if f'reject_{comment.id}' in request.POST:
                comment.is_approved = False
                comment.save()
        return redirect('consultation:moderate_comments', pk=pk)
    return render(request, 'consultation/moderate_comments.html', {'proposal': proposal, 'comments': comments})
