from django.contrib import admin
from .models import Iwi, Hapu, PasswordResetToken

# Register your models here.
admin.site.register(Iwi)
admin.site.register(Hapu)

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'expires_at', 'is_used', 'is_expired']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'user__full_name', 'token']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
