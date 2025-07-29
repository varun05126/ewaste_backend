# ewaste_backend/core/admin.py

from django.contrib import admin
from .models import PickupRequest, ContactMessage

@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    # UPDATED: Only include fields that exist in the simplified PickupRequest model
    list_display = ('name', 'email', 'phone', 'created_at')
    # Removed 'status' and 'preferred_pickup_date' as they no longer exist
    list_filter = ('created_at',)
    # Update search_fields to reflect the new model fields
    search_fields = ('name', 'email', 'phone', 'address')
    readonly_fields = ('created_at',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'submitted_at', 'read')
    list_filter = ('read', 'submitted_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('submitted_at',)
    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        queryset.update(read=True)
        self.message_user(request, "Selected messages marked as read.")
    mark_as_read.short_description = "Mark selected messages as read"

    def mark_as_unread(self, request, queryset):
        queryset.update(read=False)
        self.message_user(request, "Selected messages marked as unread.")
    mark_as_unread.short_description = "Mark selected messages as unread"