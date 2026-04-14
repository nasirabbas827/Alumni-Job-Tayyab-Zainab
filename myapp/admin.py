import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from .models import CustomUser, Profile, Job, JobApplication, JobBookmark

# ----------------------------------------------------------------
# Shared Admin Actions (Reporting)
# ----------------------------------------------------------------

def export_as_csv(modeladmin, request, queryset):
    """
    Generic action to export selected items as a CSV file.
    """
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={meta.model_name}_report_{timezone.now().strftime("%Y%m%d")}.csv'
    
    writer = csv.writer(response)
    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])

    return response

export_as_csv.short_description = "Export Selected as CSV"

# ----------------------------------------------------------------
# Model Admin Registrations
# ----------------------------------------------------------------

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'email', 'role', 'status', 'created_at')
    list_filter = ('role', 'status', 'created_at')
    search_fields = ('username', 'full_name', 'email')
    actions = [export_as_csv, 'approve_users', 'reject_users']

    @admin.action(description='Approve selected users')
    def approve_users(self, request, queryset):
        queryset.update(status='approved')

    @admin.action(description='Reject selected users')
    def reject_users(self, request, queryset):
        queryset.update(status='rejected')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'profile_visibility', 'last_updated')
    search_fields = ('user__username', 'user__full_name', 'skills')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'posted_by', 'job_type', 'status', 'posted_at', 'application_count')
    list_filter = ('status', 'job_type', 'posted_at')
    search_fields = ('title', 'description', 'posted_by__username')
    actions = [export_as_csv, 'mark_as_approved', 'mark_as_rejected', 'mark_as_closed']

    # Reporting: Show number of applications directly in the list view
    def application_count(self, obj):
        return obj.applications.count()
    application_count.short_description = 'Total Applications'

    @admin.action(description='Approve selected jobs')
    def mark_as_approved(self, request, queryset):
        queryset.update(status='approved')

    @admin.action(description='Reject selected jobs')
    def mark_as_rejected(self, request, queryset):
        queryset.update(status='rejected')
    
    @admin.action(description='Close selected jobs')
    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('applicant__full_name', 'job__title')
    actions = [export_as_csv]


@admin.register(JobBookmark)
class JobBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'bookmarked_at')
    list_filter = ('bookmarked_at',)