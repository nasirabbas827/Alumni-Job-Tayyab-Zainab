from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('login/', views.login_view, name='login'),

    path('dashboard/alumni/', views.alumni_dashboard, name='alumni_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/employer/', views.employer_dashboard, name='employer_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/update/', views.update_profile, name='update_profile'),

    path('jobs/', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:job_id>/update/', views.job_update, name='job_update'),
    path('jobs/<int:job_id>/delete/', views.job_delete, name='job_delete'),

    path('viewjobs/', views.job_board, name='job_board'),
    path('job/apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('job/bookmark/<int:job_id>/', views.toggle_bookmark, name='toggle_bookmark'),

    path('my-job-applications/', views.my_job_applications, name='my_job_applications'),
    path('application/<int:application_id>/update/', views.update_application_status, name='update_application_status'),
    path('my-applied-jobs/', views.my_applied_jobs, name='my_applied_jobs'),

    path('profile/view/<int:user_id>/', views.view_profile, name='view_profile'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),

path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset-confirm/', views.password_reset_confirm, name='password_reset_confirm'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
