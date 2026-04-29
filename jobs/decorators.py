from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def employer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access this page.")
            return redirect('login')
        if hasattr(request.user, 'profile') and request.user.profile.role == 'employer':
            return view_func(request, *args, **kwargs)
        messages.error(request, "This page is for employers only.")
        return redirect('unauthorized')
    return wrapper


def job_seeker_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access this page.")
            return redirect('login')
        if hasattr(request.user, 'profile') and request.user.profile.role == 'job_seeker':
            return view_func(request, *args, **kwargs)
        messages.error(request, "This page is for job seekers only.")
        return redirect('unauthorized')
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access this page.")
            return redirect('login')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        messages.error(request, "You don't have permission to access this page.")
        return redirect('unauthorized')
    return wrapper
