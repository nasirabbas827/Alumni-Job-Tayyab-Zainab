from django.contrib import admin
from .models import CustomUser, Profile, Job, JobApplication, JobBookmark

# ---------------- CustomUser ----------------
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'email', 'role', 'status', 'created_at')
    list_filter = ('role', 'status', 'created_at')
    search_fields = ('username', 'full_name', 'email')
    ordering = ('-created_at',)

# ---------------- Profile ----------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'profile_visibility', 'last_updated')
    search_fields = ('user__username', 'user__full_name', 'skills', 'education')
    list_filter = ('profile_visibility', 'last_updated')
    readonly_fields = ('resume_file_name', 'resume_upload_date')
    ordering = ('-last_updated',)

# ---------------- Job ----------------
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'posted_by', 'location', 'job_type', 'status', 'posted_at', 'deadline')
    list_filter = ('job_type', 'status', 'posted_at', 'deadline')
    search_fields = ('title', 'description', 'required_skills', 'location', 'posted_by__username')
    ordering = ('-posted_at',)

# ---------------- JobApplication ----------------
@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'applicant', 'status', 'applied_at', 'updated_at')
    list_filter = ('status', 'applied_at', 'updated_at')
    search_fields = ('job__title', 'applicant__full_name', 'applicant__username')
    ordering = ('-applied_at',)

# ---------------- JobBookmark ----------------
@admin.register(JobBookmark)
class JobBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'bookmarked_at')
    list_filter = ('bookmarked_at',)
    search_fields = ('user__username', 'job__title')
    ordering = ('-bookmarked_at',)
