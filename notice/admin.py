from django.contrib import admin
from .models import Notice, NoticeAcknowledgment

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'expiry_date', 'created_by', 'created_at', 'priority')
    list_filter = ('audience', 'expiry_date', 'created_by')
    search_fields = ('title', 'content')

@admin.register(NoticeAcknowledgment)
class NoticeAcknowledgmentAdmin(admin.ModelAdmin):
    list_display = ('notice', 'user', 'acknowledged_at')
    list_filter = ('notice', 'user')
