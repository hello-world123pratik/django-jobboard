from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    path('register/', views.register, name='register'),
    path('unauthorized/', views.unauthorized, name='unauthorized'),

    # Job Seeker
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('my-applications/', views.applied_jobs, name='applied_jobs'),

    # Profile
    path('profile/<int:pk>/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Employer
    path('employer/jobs/', views.employer_jobs, name='employer_jobs'),
    path('employer/jobs/new/', views.job_create, name='job_create'),
    path('employer/jobs/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('employer/applications/', views.employer_applications, name='employer_applications'),
    path('employer/applications/<int:pk>/status/', views.update_application_status, name='update_application_status'),

    # Admin moderation
    path('moderate/jobs/', views.approve_jobs, name='approve_jobs'),
    path('moderate/jobs/<int:pk>/approve/', views.approve_job, name='approve_job'),
    path('moderate/jobs/<int:pk>/reject/', views.reject_job, name='reject_job'),
]

# ── CUSTOM ADMIN PANEL ────────────────────────────────────────────────────────
from . import admin_views

urlpatterns += [
    path('panel/',                              admin_views.dashboard,           name='admin_dashboard'),
    path('panel/jobs/',                         admin_views.jobs_list,           name='admin_jobs'),
    path('panel/jobs/add/',                     admin_views.job_add,             name='admin_job_add'),
    path('panel/jobs/<int:pk>/edit/',           admin_views.job_edit,            name='admin_job_edit'),
    path('panel/jobs/<int:pk>/approve/',        admin_views.job_approve,         name='admin_job_approve'),
    path('panel/jobs/<int:pk>/delete/',         admin_views.job_delete,          name='admin_job_delete'),
    path('panel/applications/',                 admin_views.applications_list,   name='admin_applications'),
    path('panel/applications/<int:pk>/status/', admin_views.application_status,  name='admin_application_status'),
    path('panel/applications/<int:pk>/delete/', admin_views.application_delete,  name='admin_application_delete'),
    path('panel/users/',                        admin_views.users_list,          name='admin_users'),
    path('panel/users/<int:pk>/',               admin_views.user_detail,         name='admin_user_detail'),
    path('panel/users/<int:pk>/toggle/',        admin_views.user_toggle,         name='admin_user_toggle'),
    path('panel/categories/',                   admin_views.categories_list,     name='admin_categories'),
    path('panel/categories/save/',              admin_views.category_save,       name='admin_category_save'),
    path('panel/categories/<int:pk>/delete/',   admin_views.category_delete,     name='admin_category_delete'),
]
