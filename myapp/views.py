from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import CustomUser, Profile, Job, JobApplication, JobBookmark
from .forms import RegisterForm, LoginForm, ProfileForm, JobForm, JobApplicationForm


def index(request):
    jobs = Job.objects.filter(status='approved').order_by('-posted_at')[:6]
    return render(request, 'index.html', {'jobs': jobs})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']

            # Check for duplicate email
            if CustomUser.objects.filter(email=email).exists():
                form.add_error('email', "This email is already registered.")
                return render(request, 'register.html', {'form': form})

            # Check for duplicate username
            if CustomUser.objects.filter(username=username).exists():
                form.add_error('username', "This username is already taken.")
                return render(request, 'register.html', {'form': form})

            user = form.save(commit=False)
            user.status = 'pending'
            user.save()

            verification_link = f"http://127.0.0.1:8000/verify-email/?email={email}"

            try:
                send_mail(
                    subject="Verify Your Alumni Job Portal Account",
                    message=f"Hi {user.full_name},\n\n"
                            f"Thank you for registering!\n\n"
                            f"Please verify your email by clicking the link below:\n"
                            f"{verification_link}\n\n"
                            f"This link will expire in 24 hours.\n\n"
                            f"Best regards,\nAlumni Job Portal Team",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, "Registration successful. Please check your email to verify your account.")
            except Exception as e:
                messages.error(request, "Failed to send verification email. Please contact support.")

            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})



def verify_email(request):
    """
    Verifies user's email via the link sent during registration.
    Sets status to 'approved' and allows login.
    """
    email = request.GET.get('email')

    if not email:
        messages.error(request, "Invalid verification request.")
        return redirect('login')

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')

    user.status = 'approved'
    user.save()

    messages.success(request, "Your email has been verified. You can now log in.")
    return redirect('login')


# --------------------- LOGIN & LOGOUT ---------------------
def login_view(request):
    """
    Handles user login using email and password.
    - Checks credentials
    - Verifies account is approved
    - Stores user_id and role in session
    - Redirects based on role
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user = CustomUser.objects.get(email=email, password=password)
            except CustomUser.DoesNotExist:
                messages.error(request, "Incorrect email or password.")
                return redirect('login')

            if user.status != 'approved':
                messages.warning(request, "Your account is not approved. Check your email for verification.")
                return redirect('login')

            request.session['user_id'] = user.id
            request.session['role'] = user.role

            messages.success(request, "Login successful.")

            if user.role == 'alumni':
                return redirect('alumni_dashboard')
            elif user.role == 'student':
                return redirect('student_dashboard')
            else:
                return redirect('employer_dashboard')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """
    Clears the session and logs the user out.
    """
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect('login')


# --------------------- AUTH GUARD HELPERS ---------------------
def require_login(request):
    """
    Helper: Returns the logged-in user or redirects to login if not authenticated.
    """
    if 'user_id' not in request.session:
        messages.error(request, "Please login first.")
        return None
    try:
        return CustomUser.objects.get(id=request.session['user_id'])
    except CustomUser.DoesNotExist:
        messages.error(request, "User session invalid. Please login again.")
        return None


def require_login_user(request):
    """
    Alias of require_login (used in job-related views).
    """
    return require_login(request)


def require_login_profile(request):
    """
    Same as require_login, but used for profile views.
    """
    return require_login(request)


# --------------------- DASHBOARDS ---------------------
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count
from .models import Job, JobApplication, JobBookmark
from .forms import JobForm  # if needed elsewhere

def alumni_dashboard(request):
    """
    Displays the Alumni Dashboard with:
    - Personal welcome
    - Job applications (applied by the user)
    - Suggested jobs based on skills
    - Bookmarks & applied status
    - Detailed job statistics:
      - Total jobs posted by the user
      - Breakdown of job statuses (Pending, Approved, Rejected)
      - Total applications received on user's jobs
      - Total jobs the user has applied to
    """
    user = require_login(request)
    if not user:
        return redirect('login')

    if user.role != 'alumni':
        messages.error(request, "Access denied.")
        return redirect('login')

    # 1. User's own job applications (as applicant)
    applications = JobApplication.objects.filter(applicant=user).order_by('-applied_at')

    # 2. Suggested jobs based on user's profile skills
    suggested_jobs = []
    bookmarked_job_ids = []
    applied_job_ids = []

    if hasattr(user, 'profile') and user.profile.skills:
        skills = [s.strip().lower() for s in user.profile.skills.split(',') if s.strip()]
        if skills:
            # Match jobs that require any of the user's skills
            regex_pattern = '|'.join(skills)
            suggested_jobs = Job.objects.filter(
                status='approved',
                required_skills__iregex=r'(' + regex_pattern + ')'
            ).exclude(posted_by=user)

    # 3. Bookmarks and applied jobs (for action buttons)
    bookmarks = JobBookmark.objects.filter(user=user)
    bookmarked_job_ids = [b.job.id for b in bookmarks]

    applied_jobs = JobApplication.objects.filter(applicant=user)
    applied_job_ids = [a.job.id for a in applied_jobs]

    # 4. Job statistics for the user (as poster)
    user_jobs = Job.objects.filter(posted_by=user)

    total_jobs_posted = user_jobs.count()
    pending_jobs_count = user_jobs.filter(status='pending').count()
    approved_jobs_count = user_jobs.filter(status='approved').count()
    rejected_jobs_count = user_jobs.filter(status='rejected').count()

    # Total applications received on jobs posted by this user
    total_applications_received = JobApplication.objects.filter(
        job__posted_by=user
    ).count()

    # Total jobs the user has applied to (as alumni)
    total_applied_jobs = applications.count()

    context = {
        'user': user,
        'applications': applications,               # for "Your Job Applications" table
        'suggested_jobs': suggested_jobs,           # for "Suggested Jobs" table
        'bookmarked_job_ids': bookmarked_job_ids,   # for bookmark buttons
        'applied_job_ids': applied_job_ids,         # for applied status
        # Statistics for cards and pie chart
        'total_jobs_posted': total_jobs_posted,
        'pending_jobs_count': pending_jobs_count,
        'approved_jobs_count': approved_jobs_count,
        'rejected_jobs_count': rejected_jobs_count,
        'total_applications_received': total_applications_received,
        'total_applied_jobs': total_applied_jobs,
    }

    return render(request, 'dashboards/alumni_dashboard.html', context)

def student_dashboard(request):
    """
    Student Dashboard with statistics, application status chart,
    applied jobs, and suggested matches.
    """
    user = require_login(request)
    if not user:
        return redirect('login')

    if user.role != 'student':
        messages.error(request, "Access denied.")
        return redirect('login')

    # 1. Job applications made by the student
    applications = JobApplication.objects.filter(applicant=user).order_by('-applied_at')

    # 2. Application status counts for pie chart
    status_counts = applications.values('status').annotate(count=Count('status'))
    applied_count = next((item['count'] for item in status_counts if item['status'] == 'applied'), 0)
    shortlisted_count = next((item['count'] for item in status_counts if item['status'] == 'shortlisted'), 0)
    interviewed_count = next((item['count'] for item in status_counts if item['status'] == 'interviewed'), 0)
    rejected_count = next((item['count'] for item in status_counts if item['status'] == 'rejected'), 0)
    hired_count = next((item['count'] for item in status_counts if item['status'] == 'hired'), 0)

    # 3. Suggested jobs based on skills
    suggested_jobs = []
    if hasattr(user, 'profile') and user.profile.skills:
        skills = [s.strip().lower() for s in user.profile.skills.split(',') if s.strip()]
        if skills:
            regex_pattern = '|'.join(skills)
            suggested_jobs = Job.objects.filter(
                status='approved',
                required_skills__iregex=r'(' + regex_pattern + ')'
            ).exclude(posted_by=user)

    # 4. Bookmarks and applied jobs (for buttons)
    bookmarked_job_ids = [b.job.id for b in JobBookmark.objects.filter(user=user)]
    applied_job_ids = [a.job.id for a in applications]

    # 5. Statistics
    total_applied_jobs = applications.count()
    total_bookmarked_jobs = JobBookmark.objects.filter(user=user).count()
    pending_applications_count = applications.filter(status='applied').count()

    context = {
        'user': user,
        'applications': applications,
        'suggested_jobs': suggested_jobs,
        'bookmarked_job_ids': bookmarked_job_ids,
        'applied_job_ids': applied_job_ids,
        'total_applied_jobs': total_applied_jobs,
        'total_bookmarked_jobs': total_bookmarked_jobs,
        'pending_applications_count': pending_applications_count,
        'applied_count': applied_count,
        'shortlisted_count': shortlisted_count,
        'interviewed_count': interviewed_count,
        'rejected_count': rejected_count,
        'hired_count': hired_count,
    }

    return render(request, 'dashboards/student_dashboard.html', context)


def employer_dashboard(request):
    """
    Employer Dashboard with statistics, job status chart, recent postings,
    and quick actions.
    """
    user = require_login(request)
    if not user:
        return redirect('login')

    if user.role != 'employer':
        messages.error(request, "Access denied.")
        return redirect('login')

    # All jobs posted by this employer
    user_jobs = Job.objects.filter(posted_by=user)

    # Statistics
    total_jobs_posted = user_jobs.count()
    pending_jobs_count = user_jobs.filter(status='pending').count()
    approved_jobs_count = user_jobs.filter(status='approved').count()
    rejected_jobs_count = user_jobs.filter(status='rejected').count()

    total_applications_received = JobApplication.objects.filter(
        job__posted_by=user
    ).count()

    # Recent jobs (latest 10) with correct annotation using the reverse relation 'applications'
    recent_jobs = user_jobs.annotate(
        applications_count=Count('applications')   # <-- This is the correct name!
    ).order_by('-posted_at')[:10]   # or '-created_at' if your field is called created_at

    context = {
        'user': user,
        'total_jobs_posted': total_jobs_posted,
        'pending_jobs_count': pending_jobs_count,
        'approved_jobs_count': approved_jobs_count,
        'rejected_jobs_count': rejected_jobs_count,
        'total_applications_received': total_applications_received,
        'recent_jobs': recent_jobs,
    }

    return render(request, 'dashboards/employer_dashboard.html', context)


# --------------------- PROFILE MANAGEMENT ---------------------
def update_profile(request):
    """
    Allows users to update their profile (including photo, skills, etc.).
    """
    user = require_login_profile(request)
    if not user:
        return redirect('login')

    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('update_profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'profile_update.html', {
        'form': form,
        'profile': profile,
        'user': user
    })


# --------------------- JOB CRUD (Post, Edit, Delete) ---------------------
def job_list(request):
    """
    Shows all jobs posted by the current user.
    """
    user = require_login_user(request)
    if not user:
        return redirect('login')

    jobs = Job.objects.filter(posted_by=user)
    return render(request, 'jobs/job_list.html', {'jobs': jobs})


def job_create(request):
    """
    Allows alumni/employers to create a new job posting.
    Sends email notification to all students/alumni.
    """
    user = require_login_user(request)
    if not user:
        return redirect('login')

    if user.role not in ['alumni', 'employer']:
        messages.error(request, "Access denied. Only Alumni and Employers can post jobs.")
        return redirect('job_list')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = user
            job.status = 'pending'
            job.save()

            # Send email notification to all students and alumni
            recipients = CustomUser.objects.filter(role__in=['student', 'alumni'], status='approved').values_list('email', flat=True)
            if recipients:
                try:
                    send_mail(
                        subject=f"New Job Posted: {job.title}",
                        message=f"Hi there,\n\n"
                                f"A new job opportunity has been posted on the Alumni Job Portal:\n\n"
                                f"Title: {job.title}\n"
                                f"Company: {job.company_name}\n"
                                f"Location: {job.location}\n\n"
                                f"View it here: http://127.0.0.1:8000/jobs/board/\n\n"
                                f"Best regards,\nAlumni Job Portal Team",
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=recipients,
                        fail_silently=False,
                    )
                except Exception:
                    pass  # Don't block user if email fails

            messages.success(request, "Job created successfully. Awaiting approval.")
            return redirect('job_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = JobForm()

    return render(request, 'jobs/job_form.html', {'form': form, 'action': 'Create'})


def job_update(request, job_id):
    user = require_login_user(request)
    if not user:
        return redirect('login')

    job = get_object_or_404(Job, id=job_id, posted_by=user)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully.")
            return redirect('job_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = JobForm(instance=job)

    return render(request, 'jobs/job_form.html', {'form': form, 'action': 'Update'})


def job_delete(request, job_id):
    user = require_login_user(request)
    if not user:
        return redirect('login')

    job = get_object_or_404(Job, id=job_id, posted_by=user)
    job.delete()
    messages.success(request, "Job deleted successfully.")
    return redirect('job_list')


# --------------------- JOB BOARD & SEARCH ---------------------
def job_board(request):
    """
    Displays approved jobs with search, filters, and skill-based suggestions.
    """
    user = require_login_user(request)
    if not user:
        return redirect('login')

    jobs = Job.objects.filter(status='approved').exclude(posted_by=user)

    # Search filters
    query = request.GET.get('q', '')
    job_type = request.GET.get('job_type', '')
    location = request.GET.get('location', '')

    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(required_skills__icontains=query))
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if location:
        jobs = jobs.filter(location__icontains=location)

    # Suggested jobs based on user skills
    suggested_jobs = []
    if hasattr(user, 'profile') and user.profile.skills:
        skills = [s.strip().lower() for s in user.profile.skills.split(',')]
        suggested_jobs = jobs.filter(
            Q(required_skills__iregex=r'(' + '|'.join(skills) + ')')
        )

    # Bookmarks & Applications
    bookmarks = JobBookmark.objects.filter(user=user)
    bookmarked_job_ids = [b.job.id for b in bookmarks]

    user_applications = JobApplication.objects.filter(applicant=user)
    applied_job_ids = [a.job.id for a in user_applications]

    return render(request, 'jobs/job_board.html', {
        'jobs': jobs,
        'suggested_jobs': suggested_jobs,
        'bookmarked_job_ids': bookmarked_job_ids,
        'applied_job_ids': applied_job_ids,
        'user': user,
    })


def job_detail(request, job_id):
    """
    Displays detailed view of a single job.
    """
    user = require_login_user(request)
    if not user:
        return redirect('login')

    job = get_object_or_404(Job, id=job_id, status='approved')

    # Bookmarks & Applications (for buttons)
    bookmarked_job_ids = [b.job.id for b in JobBookmark.objects.filter(user=user)]
    applied_job_ids = [a.job.id for a in JobApplication.objects.filter(applicant=user)]

    context = {
        'job': job,
        'bookmarked_job_ids': bookmarked_job_ids,
        'applied_job_ids': applied_job_ids,
        'user': user,
    }
    return render(request, 'jobs/job_detail.html', context)

# --------------------- APPLY TO JOB ---------------------
def apply_job(request, job_id):
    """
    Allows users to apply to a job.
    Sends email notification to the job poster.
    """
    user = require_login_user(request)
    if not user:
        return redirect('login')

    job = get_object_or_404(Job, id=job_id, status='approved')

    if job.posted_by == user:
        messages.error(request, "You cannot apply to your own job.")
        return redirect('job_board')

    if JobApplication.objects.filter(job=job, applicant=user).exists():
        messages.warning(request, "You have already applied to this job.")
        return redirect('job_board')

    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = user
            application.save()

            # Notify job poster
            try:
                send_mail(
                    subject=f"New Application for {job.title}",
                    message=f"Hi {job.posted_by.full_name},\n\n"
                            f"{user.full_name} ({user.email}) has applied to your job posting:\n\n"
                            f"Job: {job.title}\n"
                            f"View applications: http://127.0.0.1:8000/jobs/my-applications/\n\n"
                            f"Best regards,\nAlumni Job Portal Team",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[job.posted_by.email],
                    fail_silently=False,
                )
            except Exception:
                pass

            messages.success(request, "Job application submitted successfully.")
            return redirect('job_board')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = JobApplicationForm()

    return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})


# --------------------- BOOKMARK ---------------------
def toggle_bookmark(request, job_id):
    user = require_login_user(request)
    job = get_object_or_404(Job, id=job_id, status='approved')
    bookmark, created = JobBookmark.objects.get_or_create(user=user, job=job)
    if not created:
        bookmark.delete()
        messages.info(request, "Bookmark removed.")
    else:
        messages.success(request, "Job bookmarked.")
    return redirect('job_board')


# --------------------- MY APPLICATIONS (For Job Posters) ---------------------
def my_job_applications(request):
    """
    Shows all applications received for jobs posted by the current user.
    """
    user = require_login_user(request)
    if not user:
        return redirect('login')

    if user.role not in ['alumni', 'employer']:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    jobs = Job.objects.filter(posted_by=user)
    applications = JobApplication.objects.filter(job__in=jobs).order_by('-applied_at')

    return render(request, 'jobs/my_job_applications.html', {
        'applications': applications,
        'user': user
    })


# --------------------- UPDATE APPLICATION STATUS ---------------------
def update_application_status(request, application_id):
    """
    Allows job posters to change application status.
    Sends email notification to the applicant.
    """
    user = require_login_user(request)
    if not user:
        return redirect('login')

    application = get_object_or_404(JobApplication, id=application_id)

    if application.job.posted_by != user:
        messages.error(request, "Access denied.")
        return redirect('my_job_applications')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(JobApplication.STATUS_CHOICES).keys():
            old_status = application.status
            application.status = new_status
            application.save()

            # Notify applicant
            try:
                send_mail(
                    subject=f"Update on Your Application: {application.job.title}",
                    message=f"Hi {application.applicant.full_name},\n\n"
                            f"Your application status for '{application.job.title}' has changed:\n\n"
                            f"From: {old_status}\n"
                            f"To: {new_status}\n\n"
                            f"View details: http://127.0.0.1:8000/jobs/my-applied-jobs/\n\n"
                            f"Best regards,\nAlumni Job Portal Team",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[application.applicant.email],
                    fail_silently=False,
                )
            except Exception:
                pass

            messages.success(request, "Application status updated successfully.")
        else:
            messages.error(request, "Invalid status.")
        return redirect('my_job_applications')

    return render(request, 'jobs/update_application_status.html', {
        'application': application,
        'status_choices': JobApplication.STATUS_CHOICES
    })


# --------------------- MY APPLIED JOBS (For Applicants) ---------------------
def my_applied_jobs(request):
    """
    Shows all jobs the current user has applied to.
    """
    user = require_login_user(request)
    if not user:
        return redirect('login')

    applications = JobApplication.objects.filter(applicant=user).order_by('-applied_at')

    return render(request, 'jobs/my_applied_jobs.html', {
        'applications': applications,
        'user': user
    })


# --------------------- PUBLIC PROFILE VIEW ---------------------
def view_profile(request, user_id):
    """
    Displays a public profile if visibility is set to 'Public'.
    """
    user = get_object_or_404(CustomUser, id=user_id)

    if not hasattr(user, 'profile') or user.profile.profile_visibility != 'Public':
        messages.error(request, "This profile is private.")
        return redirect('job_board')

    profile = user.profile
    return render(request, 'profile_view.html', {'profile': profile})

# --------------------- SIMPLE PASSWORD RESET ---------------------

def password_reset_request(request):
    """
    Simple password reset request:
    - User enters email
    - We check if it exists in CustomUser
    - If yes, send email with reset link containing the email
    """
    if request.method == 'POST':
        email = request.POST.get('email')

        if not email:
            messages.error(request, "Please enter your email address.")
            return render(request, 'password_reset_request.html')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "No account found with this email.")
            return render(request, 'password_reset_request.html')

        # Simple reset link (contains email as query param)
        reset_link = f"http://127.0.0.1:8000/password-reset-confirm/?email={email}"

        try:
            send_mail(
                subject="Reset Your Alumni Job Portal Password",
                message=f"Hi {user.full_name},\n\n"
                        f"You requested a password reset.\n\n"
                        f"Click the link below to set a new password:\n"
                        f"{reset_link}\n\n"
                        f"This link is valid for 24 hours.\n\n"
                        f"If you didn't request this, please ignore this email.\n\n"
                        f"Best regards,\nAlumni Job Portal Team",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, "Password reset link has been sent to your email.")
        except Exception:
            messages.error(request, "Failed to send email. Please try again later.")

        return redirect('login')

    return render(request, 'password_reset/password_reset_request.html')


def password_reset_confirm(request):
    """
    User clicks the link → enters new password twice
    """
    email = request.GET.get('email')

    if not email:
        messages.error(request, "Invalid reset link.")
        return redirect('login')

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not new_password or not confirm_password:
            messages.error(request, "Both password fields are required.")
        elif new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        else:
            user.password = new_password  # plain text – only for demo/learning
            # In production, use: user.set_password(new_password)
            user.save()
            messages.success(request, "Your password has been reset successfully. Please log in.")
            return redirect('login')

    return render(request, 'password_reset/password_reset_confirm.html', {'email': email})