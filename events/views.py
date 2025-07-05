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
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
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
        form = EventForm()
    return render(request, 'events/create_event.html', {'form': form})

@login_required
def event_list_json(request):
    # Return events as JSON for FullCalendar
    events = Event.objects.all()
    data = []
    for event in events:
        data.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_datetime.isoformat(),
            'end': event.end_datetime.isoformat(),
            'url': f'/events/{event.id}/',
        })
    return JsonResponse(data, safe=False)

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    joined = EventParticipant.objects.filter(event=event, user=request.user).exists()
    return render(request, 'events/event_detail.html', {'event': event, 'joined': joined})

@login_required
def join_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    EventParticipant.objects.get_or_create(event=event, user=request.user)
    return redirect('events:event_detail', event_id=event.id)

@login_required
def my_events(request):
    joined_events = Event.objects.filter(participants__user=request.user).order_by('start_datetime')
    return render(request, 'events/my_events.html', {'joined_events': joined_events})
