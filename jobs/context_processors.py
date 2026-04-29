def user_role(request):
    is_employer = False
    is_job_seeker = False
    is_admin = False

    if request.user.is_authenticated:
        if request.user.is_superuser:
            is_admin = True
        elif hasattr(request.user, 'profile'):
            is_employer = request.user.profile.role == 'employer'
            is_job_seeker = request.user.profile.role == 'job_seeker'

    return {
        'is_employer': is_employer,
        'is_job_seeker': is_job_seeker,
        'is_admin': is_admin,
    }
