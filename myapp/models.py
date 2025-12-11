from django.db import models

class CustomUser(models.Model):
    ROLE_CHOICES = (
        ('alumni', 'Alumni'),
        ('student', 'Student'),
        ('employer', 'Employer'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username



from django.db import models
from django.core.validators import FileExtensionValidator
from .models import CustomUser  # Using your CustomUser model

class Profile(models.Model):
    VISIBILITY_CHOICES = (
        ('Public', 'Public'),
        ('Private', 'Private'),
    )

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='profile')

    phone_number = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='Public')
    last_updated = models.DateTimeField(auto_now=True)

    skills = models.CharField(max_length=1000, blank=True, help_text="Comma-separated list of skills")
    education = models.TextField(blank=True, help_text="Describe your education")
    experience = models.TextField(blank=True, help_text="Describe your work experience")

    resume = models.FileField(
        upload_to='resumes/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        blank=True,
        null=True
    )
    resume_file_name = models.CharField(max_length=255, blank=True)
    resume_upload_date = models.DateTimeField(null=True, blank=True)

    profile_pic = models.ImageField(
        upload_to='profile_pics/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )

    def __str__(self):
        return f"Profile of {self.user.username}"



class Job(models.Model):
    JOB_TYPE_CHOICES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
        ('remote', 'Remote'),
    )

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    posted_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    salary_range_min = models.PositiveIntegerField(null=True, blank=True)
    salary_range_max = models.PositiveIntegerField(null=True, blank=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    required_skills = models.CharField(max_length=500, blank=True, help_text="Comma-separated skills")
    posted_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    def __str__(self):
        return self.title


from django.db import models
from .models import CustomUser, Job  # assuming Job and CustomUser are in the same app


# ------------------ Job Applications ------------------
class JobApplication(models.Model):
    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('interviewed', 'Interviewed'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    resume = models.FileField(upload_to='job_applications/%Y/%m/%d/', null=True, blank=True)
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job', 'applicant')

    def __str__(self):
        return f"{self.applicant.full_name} applied to {self.job.title}"


# ------------------ Job Bookmarks ------------------
class JobBookmark(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookmarks')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='bookmarks')
    bookmarked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.full_name} bookmarked {self.job.title}"


