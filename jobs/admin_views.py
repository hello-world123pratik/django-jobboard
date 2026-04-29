import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta

from .models import Job, Application, Profile, Category, JOB_TYPE_CHOICES
from .forms import JobForm
from .decorators import admin_required


def _base_ctx(request):
    """Shared context injected into every admin view."""
    pending_count = Job.objects.filter(is_approved=False).count()
    return {'pending_count': pending_count}


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@admin_required
def dashboard(request):
    now = timezone.now()
    week_ago = now - timedelta(days=7)

    total_jobs      = Job.objects.count()
    approved_jobs   = Job.objects.filter(is_approved=True).count()
    pending_jobs    = Job.objects.filter(is_approved=False).count()
    total_apps      = Application.objects.count()
    new_apps        = Application.objects.filter(created_at__gte=week_ago).count()
    total_users     = User.objects.count()
    new_users       = User.objects.filter(date_joined__gte=week_ago).count()
    total_employers = Profile.objects.filter(role='employer').count()
    total_seekers   = Profile.objects.filter(role='job_seeker').count()

    # Chart: jobs by type
    type_qs = (Job.objects.filter(is_approved=True)
               .values('job_type').annotate(c=Count('id')))
    type_map = {r['job_type']: r['c'] for r in type_qs}
    job_type_labels = [lbl for _, lbl in JOB_TYPE_CHOICES]
    job_type_data   = [type_map.get(val, 0) for val, _ in JOB_TYPE_CHOICES]

    # Chart: application status
    status_colors = {
        'pending': '#d97706', 'reviewed': '#3b82f6',
        'shortlisted': '#16a34a', 'rejected': '#dc2626',
    }
    status_qs = Application.objects.values('status').annotate(c=Count('id'))
    status_map = {r['status']: r['c'] for r in status_qs}
    total_apps_nz = max(total_apps, 1)
    app_status_data = [
        {
            'label': lbl,
            'count': status_map.get(val, 0),
            'pct':   round(status_map.get(val, 0) / total_apps_nz * 100),
            'color': status_colors.get(val, '#94a3b8'),
        }
        for val, lbl in Application.STATUS_CHOICES
    ]
    app_status_labels = [d['label'] for d in app_status_data]
    app_status_counts = [d['count'] for d in app_status_data]

    top_jobs = (Job.objects.filter(is_approved=True)
                .annotate(app_count=Count('application'))
                .order_by('-app_count')[:5])

    recent_apps  = Application.objects.select_related('user', 'job').order_by('-created_at')[:7]
    recent_users = User.objects.select_related('profile').order_by('-date_joined')[:7]

    ctx = {
        **_base_ctx(request),
        'total_jobs': total_jobs, 'approved_jobs': approved_jobs,
        'pending_jobs': pending_jobs, 'total_applications': total_apps,
        'new_applications': new_apps, 'total_users': total_users,
        'new_users': new_users, 'total_employers': total_employers,
        'total_seekers': total_seekers,
        'job_type_labels': job_type_labels, 'job_type_data': job_type_data,
        'app_status_data': app_status_data,
        'app_status_labels': app_status_labels,
        'app_status_counts': app_status_counts,
        'top_jobs': top_jobs, 'recent_apps': recent_apps,
        'recent_users': recent_users,
    }
    return render(request, 'admin_panel/dashboard.html', ctx)


# ── JOBS ──────────────────────────────────────────────────────────────────────

@admin_required
def jobs_list(request):
    # Bulk action
    if request.method == 'POST':
        action  = request.POST.get('bulk_action')
        pks     = request.POST.getlist('selected_jobs')
        if pks and action == 'approve':
            updated = Job.objects.filter(pk__in=pks).update(is_approved=True)
            messages.success(request, f'{updated} job(s) approved.')
        elif pks and action == 'reject':
            count = Job.objects.filter(pk__in=pks).count()
            Job.objects.filter(pk__in=pks).delete()
            messages.success(request, f'{count} job(s) deleted.')
        return redirect('admin_jobs')

    qs      = Job.objects.select_related('category', 'posted_by').annotate(app_count=Count('application'))
    query   = request.GET.get('q', '').strip()
    f       = request.GET.get('filter', '')
    jt      = request.GET.get('job_type', '')
    cat_id  = request.GET.get('category', '')

    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(company_name__icontains=query) | Q(location__icontains=query))
    if f == 'pending':
        qs = qs.filter(is_approved=False)
    elif f == 'approved':
        qs = qs.filter(is_approved=True)
    if jt:
        qs = qs.filter(job_type=jt)
    if cat_id:
        qs = qs.filter(category__id=cat_id)

    qs = qs.order_by('-created_at')
    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))

    ctx = {
        **_base_ctx(request),
        'jobs': page_obj, 'page_obj': page_obj,
        'total_count': qs.count(),
        'query': query, 'filter': f,
        'job_type': jt, 'selected_category': cat_id,
        'job_type_choices': JOB_TYPE_CHOICES,
        'categories': Category.objects.all(),
    }
    return render(request, 'admin_panel/jobs.html', ctx)


@admin_required
def job_add(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by    = request.user
            job.is_approved  = 'is_approved' in request.POST
            job.save()
            messages.success(request, f'Job "{job.title}" created successfully.')
            return redirect('admin_jobs')
    else:
        form = JobForm()
    return render(request, 'admin_panel/job_form.html', {
        **_base_ctx(request), 'form': form, 'action': 'Create',
    })


@admin_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            j = form.save(commit=False)
            j.is_approved = 'is_approved' in request.POST
            j.save()
            messages.success(request, f'Job "{j.title}" updated.')
            return redirect('admin_jobs')
    else:
        form = JobForm(instance=job)
    return render(request, 'admin_panel/job_form.html', {
        **_base_ctx(request), 'form': form, 'job': job, 'action': 'Edit',
    })


@admin_required
def job_approve(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        job.is_approved = True
        job.save()
        messages.success(request, f'"{job.title}" is now live.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_jobs'))


@admin_required
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        title = job.title
        job.delete()
        messages.success(request, f'"{title}" deleted.')
    return redirect('admin_jobs')


# ── APPLICATIONS ──────────────────────────────────────────────────────────────

@admin_required
def applications_list(request):
    qs = Application.objects.select_related('user', 'job', 'job__category').order_by('-created_at')
    query       = request.GET.get('q', '').strip()
    status_f    = request.GET.get('status', '')
    job_f       = request.GET.get('job', '')

    if query:
        qs = qs.filter(Q(user__username__icontains=query) | Q(user__email__icontains=query) | Q(job__title__icontains=query))
    if status_f:
        qs = qs.filter(status=status_f)
    if job_f:
        qs = qs.filter(job__pk=job_f)

    # CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="applications.csv"'
        writer = csv.writer(response)
        writer.writerow(['Applicant', 'Email', 'Job', 'Company', 'Status', 'Applied'])
        for app in qs:
            writer.writerow([app.user.username, app.user.email, app.job.title,
                             app.job.company_name, app.status, app.created_at.strftime('%Y-%m-%d')])
        return response

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))

    ctx = {
        **_base_ctx(request),
        'applications': page_obj, 'page_obj': page_obj,
        'total_count': qs.count(),
        'query': query, 'status_filter': status_f, 'job_filter': job_f,
        'status_choices': Application.STATUS_CHOICES,
        'all_jobs': Job.objects.all().order_by('title'),
    }
    return render(request, 'admin_panel/applications.html', ctx)


@admin_required
def application_status(request, pk):
    app = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Application.STATUS_CHOICES):
            app.status = new_status
            app.save()
            messages.success(request, f'Status updated to "{app.get_status_display()}".')
    return redirect(request.META.get('HTTP_REFERER', 'admin_applications'))


@admin_required
def application_delete(request, pk):
    app = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        app.delete()
        messages.success(request, 'Application deleted.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_applications'))


# ── USERS ─────────────────────────────────────────────────────────────────────

@admin_required
def users_list(request):
    qs = (User.objects.select_related('profile')
          .annotate(job_count=Count('posted_jobs'), app_count=Count('application'))
          .order_by('-date_joined'))

    query     = request.GET.get('q', '').strip()
    role_f    = request.GET.get('role', '')

    if query:
        qs = qs.filter(Q(username__icontains=query) | Q(email__icontains=query))
    if role_f:
        qs = qs.filter(profile__role=role_f)

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))

    ctx = {
        **_base_ctx(request),
        'users': page_obj, 'page_obj': page_obj,
        'total_count':    qs.count(),
        'employer_count': Profile.objects.filter(role='employer').count(),
        'seeker_count':   Profile.objects.filter(role='job_seeker').count(),
        'query': query, 'role_filter': role_f,
    }
    return render(request, 'admin_panel/users.html', ctx)


@admin_required
def user_detail(request, pk):
    profile_user = get_object_or_404(User.objects.select_related('profile'), pk=pk)
    role = getattr(profile_user, 'profile', None) and profile_user.profile.role

    jobs         = Job.objects.filter(posted_by=profile_user).annotate(app_count=Count('application'))
    applications = Application.objects.filter(user=profile_user).select_related('job')

    detail_rows = [
        {'icon': 'calendar3',        'label': 'Joined',    'value': profile_user.date_joined.strftime('%b %d, %Y')},
        {'icon': 'check-circle',     'label': 'Active',    'value': 'Yes' if profile_user.is_active else 'No'},
        {'icon': 'telephone',        'label': 'Phone',     'value': profile_user.profile.phone    or '—'},
        {'icon': 'geo-alt',          'label': 'Location',  'value': profile_user.profile.location or '—'},
        {'icon': 'globe',            'label': 'Website',   'value': profile_user.profile.website  or '—'},
        {'icon': 'file-earmark-person', 'label': 'Resume', 'value': 'Uploaded' if profile_user.profile.resume else '—'},
    ]

    ctx = {
        **_base_ctx(request),
        'profile_user': profile_user,
        'jobs': jobs, 'applications': applications,
        'detail_rows': detail_rows,
    }
    return render(request, 'admin_panel/user_detail.html', ctx)


@admin_required
def user_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST' and user != request.user:
        user.is_active = not user.is_active
        user.save()
        state = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User "{user.username}" {state}.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_users'))


# ── CATEGORIES ────────────────────────────────────────────────────────────────

@admin_required
def categories_list(request):
    cats = Category.objects.annotate(job_count=Count('job')).order_by('name')
    ctx  = {**_base_ctx(request), 'categories': cats}
    return render(request, 'admin_panel/categories.html', ctx)


@admin_required
def category_save(request):
    if request.method == 'POST':
        name   = request.POST.get('name', '').strip()
        cat_id = request.POST.get('cat_id', '').strip()
        if not name:
            messages.error(request, 'Category name cannot be empty.')
            return redirect('admin_categories')
        if cat_id:
            cat = get_object_or_404(Category, pk=cat_id)
            cat.name = name
            cat.save()
            messages.success(request, f'Category "{name}" updated.')
        else:
            if Category.objects.filter(name__iexact=name).exists():
                messages.warning(request, f'Category "{name}" already exists.')
            else:
                Category.objects.create(name=name)
                messages.success(request, f'Category "{name}" created.')
    return redirect('admin_categories')


@admin_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = cat.name
        cat.delete()
        messages.success(request, f'Category "{name}" deleted.')
    return redirect('admin_categories')
