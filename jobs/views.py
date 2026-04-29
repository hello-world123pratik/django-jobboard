from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Job, Application, Profile, Category
from .forms import JobForm, UserRegisterForm, ProfileForm
from .decorators import employer_required, job_seeker_required, admin_required


# ─────────────────────────────────────────────
# PUBLIC VIEWS
# ─────────────────────────────────────────────

def home(request):
    recent_jobs = Job.objects.filter(is_approved=True).select_related('category')[:6]
    total_jobs = Job.objects.filter(is_approved=True).count()
    total_companies = Job.objects.filter(is_approved=True).values('company_name').distinct().count()
    categories = Category.objects.annotate(job_count=Count('job')).filter(job_count__gt=0)[:8]
    return render(request, 'jobs/home.html', {
        'recent_jobs': recent_jobs,
        'total_jobs': total_jobs,
        'total_companies': total_companies,
        'categories': categories,
    })


def job_list(request):
    jobs = Job.objects.filter(is_approved=True).select_related('category')
    query = request.GET.get('q', '').strip()
    location = request.GET.get('location', '').strip()
    job_type = request.GET.get('job_type', '').strip()
    category_id = request.GET.get('category', '').strip()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(company_name__icontains=query) |
            Q(description__icontains=query)
        )
    if location:
        jobs = jobs.filter(location__icontains=location)
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if category_id:
        jobs = jobs.filter(category__id=category_id)

    paginator = Paginator(jobs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    from .models import JOB_TYPE_CHOICES

    return render(request, 'jobs/job_list.html', {
        'jobs': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'job_type_choices': JOB_TYPE_CHOICES,
        'query': query,
        'location': location,
        'selected_type': job_type,
        'selected_category': category_id,
        'total_results': jobs.count(),
    })


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_approved=True)
    has_applied = False
    if request.user.is_authenticated:
        has_applied = Application.objects.filter(job=job, user=request.user).exists()
    related_jobs = Job.objects.filter(
        is_approved=True, category=job.category
    ).exclude(pk=pk)[:3]
    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'has_applied': has_applied,
        'related_jobs': related_jobs,
    })


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to JobBoard, {user.username}! Your account has been created.")
            if hasattr(user, 'profile') and user.profile.role == 'employer':
                return redirect('employer_jobs')
            return redirect('job_list')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def unauthorized(request):
    return render(request, 'jobs/unauthorized.html')


# ─────────────────────────────────────────────
# EMPLOYER VIEWS
# ─────────────────────────────────────────────

@employer_required
def employer_jobs(request):
    jobs = Job.objects.filter(posted_by=request.user).annotate(
        app_count=Count('application')
    ).order_by('-created_at')
    return render(request, 'jobs/employer_jobs.html', {'jobs': jobs})


@employer_required
def job_create(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.is_approved = False
            job.save()
            messages.success(request, "Job posted successfully! It will be visible once approved by an admin.")
            return redirect('employer_jobs')
    else:
        form = JobForm()
    return render(request, 'jobs/job_form.html', {'form': form, 'action': 'Create'})


@employer_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully.")
            return redirect('employer_jobs')
    else:
        form = JobForm(instance=job)
    return render(request, 'jobs/job_form.html', {'form': form, 'job': job, 'action': 'Edit'})


@employer_required
def employer_applications(request):
    jobs = Job.objects.filter(posted_by=request.user)
    applications = Application.objects.filter(
        job__in=jobs
    ).select_related('job', 'user', 'user__profile').order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        applications = applications.filter(status=status_filter)
    return render(request, 'employer/applications.html', {
        'applications': applications,
        'status_filter': status_filter,
        'status_choices': Application.STATUS_CHOICES,
    })


@employer_required
def update_application_status(request, pk):
    application = get_object_or_404(Application, pk=pk, job__posted_by=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Application.STATUS_CHOICES):
            application.status = new_status
            application.save()
            messages.success(request, f"Application status updated to '{application.get_status_display()}'.")
    return redirect('employer_applications')


# ─────────────────────────────────────────────
# ADMIN VIEWS
# ─────────────────────────────────────────────

@admin_required
def approve_jobs(request):
    pending_jobs = Job.objects.filter(is_approved=False).select_related('posted_by', 'category')
    approved_jobs = Job.objects.filter(is_approved=True).select_related('posted_by', 'category')[:10]
    return render(request, 'jobs/approve_jobs.html', {
        'pending_jobs': pending_jobs,
        'approved_jobs': approved_jobs,
    })


@admin_required
def approve_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        job.is_approved = True
        job.save()
        messages.success(request, f'"{job.title}" has been approved and is now live.')
    return redirect('approve_jobs')


@admin_required
def reject_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        title = job.title
        job.delete()
        messages.success(request, f'"{title}" has been rejected and removed.')
    return redirect('approve_jobs')


# ─────────────────────────────────────────────
# JOB APPLICATIONS
# ─────────────────────────────────────────────

@job_seeker_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_approved=True)

    if Application.objects.filter(job=job, user=request.user).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('job_detail', pk=job.id)

    if request.method == 'POST':
        resume = request.FILES.get('resume')
        cover_letter = request.POST.get('cover_letter', '').strip()

        if not cover_letter:
            messages.error(request, 'Please write a cover letter.')
            return render(request, 'jobs/apply.html', {'job': job})

        Application.objects.create(
            user=request.user,
            job=job,
            resume=resume,
            cover_letter=cover_letter
        )
        messages.success(request, f'Application submitted successfully for "{job.title}"!')
        return redirect('applied_jobs')

    return render(request, 'jobs/apply.html', {'job': job})


@login_required
def applied_jobs(request):
    applications = Application.objects.filter(
        user=request.user
    ).select_related('job', 'job__category').order_by('-created_at')
    return render(request, 'jobs/applied_jobs.html', {'applications': applications})


# ─────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────

@login_required
def profile(request, pk):
    profile_obj = get_object_or_404(Profile, user__pk=pk)
    is_own = (request.user.pk == pk)
    is_admin_user = request.user.is_superuser

    # Job seeker: show recent applications
    recent_applications = None
    if is_own and profile_obj.is_job_seeker():
        recent_applications = Application.objects.filter(
            user=request.user
        ).select_related('job')[:5]

    # Employer: show job/applicant counts and recent listings
    employer_job_count = 0
    employer_app_count = 0
    employer_recent_jobs = []
    if is_own and profile_obj.is_employer():
        employer_jobs_qs = Job.objects.filter(posted_by=request.user)
        employer_job_count = employer_jobs_qs.count()
        employer_app_count = Application.objects.filter(job__in=employer_jobs_qs).count()
        employer_recent_jobs = employer_jobs_qs.order_by('-created_at')[:5]

    return render(request, 'accounts/profile.html', {
        'profile': profile_obj,
        'is_own': is_own,
        'is_admin_user': is_admin_user,
        'recent_applications': recent_applications,
        'employer_job_count': employer_job_count,
        'employer_app_count': employer_app_count,
        'employer_recent_jobs': employer_recent_jobs,
    })


@login_required
def edit_profile(request):
    profile_obj = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile', pk=request.user.pk)
    else:
        form = ProfileForm(instance=profile_obj)
    return render(request, 'accounts/edit_profile.html', {
        'form': form,
        'profile': profile_obj,
        'is_admin_user': request.user.is_superuser,
        'is_employer': profile_obj.is_employer(),
        'is_job_seeker': profile_obj.is_job_seeker(),
    })
