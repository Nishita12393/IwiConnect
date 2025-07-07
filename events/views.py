from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from .models import Event, EventParticipant
from .forms import EventForm
from django.utils import timezone

# Helper to check if user is admin or leader
from core.models import IwiLeader, HapuLeader

def is_leader_or_admin(user):
    return user.is_authenticated and (user.is_staff or IwiLeader.objects.filter(user=user).exists() or HapuLeader.objects.filter(user=user).exists())

@login_required
def event_calendar(request):
    return render(request, 'events/event_calendar.html')

@login_required
@user_passes_test(is_leader_or_admin)
def create_event(request):
    # Get current datetime for minimum event date/time
    current_datetime = timezone.now().strftime('%Y-%m-%dT%H:%M')
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('events:event_calendar')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
            return redirect('events:create_event')
    else:
        form = EventForm(user=request.user)
    return render(request, 'events/create_event.html', {
        'form': form,
        'min_datetime': current_datetime,
    })

@login_required
def event_list_json(request):
    # Return events as JSON for FullCalendar
    events = Event.objects.all()
    data = []
    for event in events:
        # Determine location display text
        if event.location_type == 'PHYSICAL':
            location_text = event.location or 'Location TBA'
        elif event.location_type == 'ONLINE':
            location_text = 'Online Event'
        else:
            location_text = 'Location TBA'
            
        data.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_datetime.isoformat(),
            'end': event.end_datetime.isoformat(),
            'url': f'/events/{event.id}/',
            'location': location_text,
            'location_type': event.location_type,
        })
    return JsonResponse(data, safe=False)

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    joined = EventParticipant.objects.filter(event=event, user=request.user).exists()
    
    # Get attendee count
    attendee_count = event.participants.count()
    
    # Check if user can view attendees (admin, event creator, or iwi/hapu leader)
    can_view_attendees = (request.user.is_staff or 
                         event.created_by == request.user or 
                         is_leader_or_admin(request.user))
    
    return render(request, 'events/event_detail.html', {
        'event': event, 
        'joined': joined,
        'attendee_count': attendee_count,
        'can_view_attendees': can_view_attendees,
    })

@login_required
def join_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    EventParticipant.objects.get_or_create(event=event, user=request.user)
    return redirect('events:event_detail', event_id=event.id)

@login_required
def my_events(request):
    joined_events = Event.objects.filter(participants__user=request.user).order_by('start_datetime')
    return render(request, 'events/my_events.html', {'joined_events': joined_events})

@login_required
def event_attendees(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user has permission to view attendees
    if not (request.user.is_staff or 
            event.created_by == request.user or 
            is_leader_or_admin(request.user)):
        messages.error(request, 'You do not have permission to view event attendees.')
        return redirect('events:event_detail', event_id=event.id)
    
    # Get all attendees with pagination
    from django.core.paginator import Paginator
    attendees = event.participants.select_related('user').order_by('joined_at')
    
    paginator = Paginator(attendees, 20)  # 20 attendees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'events/event_attendees.html', {
        'event': event,
        'page_obj': page_obj,
        'attendee_count': event.participants.count(),
    })
