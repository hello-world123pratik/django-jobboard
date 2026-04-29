from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Job, Category, Application, Profile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'job_count')
    search_fields = ('name',)

    def job_count(self, obj):
        count = obj.job_set.count()
        return format_html('<b>{}</b>', count)
    job_count.short_description = 'Jobs'


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'location', 'job_type', 'category',
                    'posted_by', 'is_approved', 'application_count', 'created_at')
    list_filter = ('is_approved', 'job_type', 'category', 'created_at')
    search_fields = ('title', 'company_name', 'description', 'location')
    list_editable = ('is_approved',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'posted_by')
    actions = ['approve_selected', 'reject_selected']

    fieldsets = (
        ('Job Details', {
            'fields': ('title', 'company_name', 'location', 'job_type', 'category', 'experience', 'salary')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Meta', {
            'fields': ('posted_by', 'is_approved', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def approval_badge(self, obj):
        if obj.is_approved:
            return format_html('<span style="color:green;font-weight:bold;">✔ Approved</span>')
        return format_html('<span style="color:orange;font-weight:bold;">⏳ Pending</span>')
    approval_badge.short_description = 'Status'

    def application_count(self, obj):
        count = obj.application_set.count()
        url = reverse('admin:jobs_application_changelist') + f'?job__id={obj.pk}'
        return format_html('<a href="{}">{} apps</a>', url, count)
    application_count.short_description = 'Applications'

    def approve_selected(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} job(s) approved successfully.')
    approve_selected.short_description = 'Approve selected jobs'

    def reject_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} job(s) rejected and deleted.')
    reject_selected.short_description = 'Reject & delete selected jobs'


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant_name', 'job_title', 'company', 'status', 'has_resume', 'created_at')
    list_filter = ('status', 'created_at', 'job__company_name')
    search_fields = ('user__username', 'user__email', 'job__title', 'job__company_name')
    list_editable = ('status',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def applicant_name(self, obj):
        return format_html('<b>{}</b><br><small>{}</small>', obj.user.username, obj.user.email)
    applicant_name.short_description = 'Applicant'

    def job_title(self, obj):
        url = reverse('admin:jobs_job_change', args=[obj.job.pk])
        return format_html('<a href="{}">{}</a>', url, obj.job.title)
    job_title.short_description = 'Job'

    def company(self, obj):
        return obj.job.company_name
    company.short_description = 'Company'

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'reviewed': 'blue',
            'shortlisted': 'green',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def has_resume(self, obj):
        if obj.resume:
            return format_html('<a href="{}" target="_blank">📄 Download</a>', obj.resume.url)
        return '—'
    has_resume.short_description = 'Resume'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role_badge', 'has_resume', 'skills_preview')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'skills')
    readonly_fields = ('user',)

    def username(self, obj):
        return obj.user.username
    username.short_description = 'Username'

    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'

    def role_badge(self, obj):
        color = 'blue' if obj.role == 'employer' else 'green'
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Role'

    def has_resume(self, obj):
        return '✔' if obj.resume else '—'
    has_resume.short_description = 'Resume'

    def skills_preview(self, obj):
        return (obj.skills[:50] + '…') if len(obj.skills) > 50 else obj.skills or '—'
    skills_preview.short_description = 'Skills'


# Customize admin site branding
admin.site.site_header = "JobBoard Administration"
admin.site.site_title = "JobBoard Admin"
admin.site.index_title = "Welcome to JobBoard Admin Panel"
