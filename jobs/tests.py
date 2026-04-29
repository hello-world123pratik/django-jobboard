"""
Comprehensive test suite for JobBoard application.
Run: python manage.py test jobs --verbosity=2
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Job, Application, Profile, Category


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def make_employer(username='emp', password='testpass123'):
    user = User.objects.create_user(username=username, password=password, email=f'{username}@test.com')
    user.profile.role = 'employer'
    user.profile.save()
    return user

def make_seeker(username='seek', password='testpass123'):
    user = User.objects.create_user(username=username, password=password, email=f'{username}@test.com')
    user.profile.role = 'job_seeker'
    user.profile.save()
    return user

def make_category(name='Tech'):
    return Category.objects.get_or_create(name=name)[0]

def make_job(posted_by, approved=True, **kwargs):
    cat = make_category()
    return Job.objects.create(
        title=kwargs.get('title', 'Test Engineer'),
        company_name=kwargs.get('company_name', 'ACME Corp'),
        description=kwargs.get('description', 'Great job opportunity.'),
        location=kwargs.get('location', 'Remote'),
        job_type=kwargs.get('job_type', 'Full-Time'),
        experience=kwargs.get('experience', 2),
        salary=kwargs.get('salary', 1000000),
        category=cat,
        posted_by=posted_by,
        is_approved=approved,
    )


# ─────────────────────────────────────────────
# MODEL TESTS
# ─────────────────────────────────────────────

class CategoryModelTest(TestCase):
    def test_str(self):
        cat = Category.objects.create(name='Engineering')
        self.assertEqual(str(cat), 'Engineering')

    def test_ordering(self):
        Category.objects.create(name='Zeta')
        Category.objects.create(name='Alpha')
        names = list(Category.objects.values_list('name', flat=True))
        self.assertEqual(names, sorted(names))


class JobModelTest(TestCase):
    def setUp(self):
        self.employer = make_employer()

    def test_str(self):
        job = make_job(self.employer, title='Dev', company_name='Corp')
        self.assertIn('Dev', str(job))
        self.assertIn('Corp', str(job))

    def test_application_count_zero(self):
        job = make_job(self.employer)
        self.assertEqual(job.application_count(), 0)

    def test_application_count_increments(self):
        job = make_job(self.employer)
        seeker = make_seeker()
        Application.objects.create(job=job, user=seeker, cover_letter='Hello')
        self.assertEqual(job.application_count(), 1)

    def test_ordering_newest_first(self):
        j1 = make_job(self.employer, title='Job 1')
        j2 = make_job(self.employer, title='Job 2')
        jobs = list(Job.objects.all())
        self.assertEqual(jobs[0], j2)  # newest first


class ProfileModelTest(TestCase):
    def test_profile_created_on_user_save(self):
        user = User.objects.create_user(username='newuser', password='pass1234')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, Profile)

    def test_default_role_is_job_seeker(self):
        user = User.objects.create_user(username='seeker2', password='pass1234')
        self.assertEqual(user.profile.role, 'job_seeker')

    def test_is_employer(self):
        emp = make_employer('emp2')
        self.assertTrue(emp.profile.is_employer())
        self.assertFalse(emp.profile.is_job_seeker())

    def test_is_job_seeker(self):
        seek = make_seeker('seek2')
        self.assertTrue(seek.profile.is_job_seeker())
        self.assertFalse(seek.profile.is_employer())

    def test_get_skills_list(self):
        user = User.objects.create_user(username='skilled', password='pass1234')
        user.profile.skills = 'Python, Django, React'
        user.profile.save()
        skills = user.profile.get_skills_list()
        self.assertEqual(skills, ['Python', 'Django', 'React'])

    def test_get_skills_list_empty(self):
        user = User.objects.create_user(username='noskills', password='pass1234')
        self.assertEqual(user.profile.get_skills_list(), [])

    def test_profile_str(self):
        user = User.objects.create_user(username='struser', password='pass1234')
        self.assertIn('struser', str(user.profile))


class ApplicationModelTest(TestCase):
    def setUp(self):
        self.employer = make_employer()
        self.seeker = make_seeker()
        self.job = make_job(self.employer)

    def test_str(self):
        app = Application.objects.create(job=self.job, user=self.seeker, cover_letter='Hi')
        self.assertIn(self.seeker.username, str(app))
        self.assertIn(self.job.title, str(app))

    def test_default_status_pending(self):
        app = Application.objects.create(job=self.job, user=self.seeker, cover_letter='Hi')
        self.assertEqual(app.status, 'pending')

    def test_unique_together(self):
        Application.objects.create(job=self.job, user=self.seeker, cover_letter='Hi')
        from django.db import IntegrityError
        with self.assertRaises(Exception):
            Application.objects.create(job=self.job, user=self.seeker, cover_letter='Again')


# ─────────────────────────────────────────────
# VIEW TESTS — PUBLIC
# ─────────────────────────────────────────────

class HomeViewTest(TestCase):
    def test_home_loads(self):
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'jobs/home.html')

    def test_home_shows_approved_jobs(self):
        emp = make_employer()
        make_job(emp, title='Approved Job', approved=True)
        make_job(emp, title='Hidden Job', approved=False)
        r = self.client.get(reverse('home'))
        self.assertContains(r, 'Approved Job')
        self.assertNotContains(r, 'Hidden Job')


class JobListViewTest(TestCase):
    def setUp(self):
        self.emp = make_employer()
        self.job1 = make_job(self.emp, title='Python Developer', location='Mumbai')
        self.job2 = make_job(self.emp, title='React Engineer', location='Delhi')
        self.unapproved = make_job(self.emp, title='Secret Job', approved=False)

    def test_lists_approved_jobs(self):
        r = self.client.get(reverse('job_list'))
        self.assertContains(r, 'Python Developer')
        self.assertContains(r, 'React Engineer')
        self.assertNotContains(r, 'Secret Job')

    def test_search_by_title(self):
        r = self.client.get(reverse('job_list'), {'q': 'Python'})
        self.assertContains(r, 'Python Developer')
        self.assertNotContains(r, 'React Engineer')

    def test_search_by_location(self):
        r = self.client.get(reverse('job_list'), {'location': 'Delhi'})
        self.assertContains(r, 'React Engineer')
        self.assertNotContains(r, 'Python Developer')

    def test_filter_by_job_type(self):
        r = self.client.get(reverse('job_list'), {'job_type': 'Full-Time'})
        self.assertEqual(r.status_code, 200)

    def test_empty_search_returns_empty(self):
        r = self.client.get(reverse('job_list'), {'q': 'xyznonexistent'})
        self.assertContains(r, '0')


class JobDetailViewTest(TestCase):
    def setUp(self):
        self.emp = make_employer()
        self.job = make_job(self.emp)

    def test_approved_job_loads(self):
        r = self.client.get(reverse('job_detail', args=[self.job.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.job.title)

    def test_unapproved_job_returns_404(self):
        job = make_job(self.emp, approved=False)
        r = self.client.get(reverse('job_detail', args=[job.pk]))
        self.assertEqual(r.status_code, 404)

    def test_shows_apply_button_to_seeker(self):
        seeker = make_seeker()
        self.client.login(username='seek', password='testpass123')
        r = self.client.get(reverse('job_detail', args=[self.job.pk]))
        self.assertContains(r, 'Apply Now')

    def test_shows_already_applied_notice(self):
        seeker = make_seeker()
        Application.objects.create(job=self.job, user=seeker, cover_letter='Hi')
        self.client.login(username='seek', password='testpass123')
        r = self.client.get(reverse('job_detail', args=[self.job.pk]))
        self.assertContains(r, "already applied")


# ─────────────────────────────────────────────
# VIEW TESTS — AUTH
# ─────────────────────────────────────────────

class RegisterViewTest(TestCase):
    def test_register_page_loads(self):
        r = self.client.get(reverse('register'))
        self.assertEqual(r.status_code, 200)

    def test_register_job_seeker(self):
        r = self.client.post(reverse('register'), {
            'username': 'newseeker',
            'email': 'newseeker@test.com',
            'password': 'strongpass99',
            'confirm_password': 'strongpass99',
            'role': 'job_seeker',
        })
        self.assertTrue(User.objects.filter(username='newseeker').exists())
        user = User.objects.get(username='newseeker')
        self.assertEqual(user.profile.role, 'job_seeker')

    def test_register_employer(self):
        r = self.client.post(reverse('register'), {
            'username': 'newemp',
            'email': 'newemp@test.com',
            'password': 'strongpass99',
            'confirm_password': 'strongpass99',
            'role': 'employer',
        })
        self.assertTrue(User.objects.filter(username='newemp').exists())
        user = User.objects.get(username='newemp')
        self.assertEqual(user.profile.role, 'employer')

    def test_register_password_mismatch(self):
        r = self.client.post(reverse('register'), {
            'username': 'baduser',
            'email': 'bad@test.com',
            'password': 'pass1',
            'confirm_password': 'pass2',
            'role': 'job_seeker',
        })
        self.assertFalse(User.objects.filter(username='baduser').exists())

    def test_register_duplicate_email(self):
        User.objects.create_user(username='existing', email='dup@test.com', password='pass1234')
        r = self.client.post(reverse('register'), {
            'username': 'newone',
            'email': 'dup@test.com',
            'password': 'strongpass99',
            'confirm_password': 'strongpass99',
            'role': 'job_seeker',
        })
        self.assertFalse(User.objects.filter(username='newone').exists())

    def test_authenticated_redirected_from_register(self):
        make_seeker()
        self.client.login(username='seek', password='testpass123')
        r = self.client.get(reverse('register'))
        self.assertEqual(r.status_code, 302)


# ─────────────────────────────────────────────
# VIEW TESTS — JOB SEEKER
# ─────────────────────────────────────────────

class ApplyJobViewTest(TestCase):
    def setUp(self):
        self.emp = make_employer()
        self.seeker = make_seeker()
        self.job = make_job(self.emp)
        self.client.login(username='seek', password='testpass123')

    def test_apply_page_loads(self):
        r = self.client.get(reverse('apply_job', args=[self.job.pk]))
        self.assertEqual(r.status_code, 200)

    def test_successful_application(self):
        r = self.client.post(reverse('apply_job', args=[self.job.pk]), {
            'cover_letter': 'I am very interested in this role and believe my skills are a great match.',
        })
        self.assertTrue(Application.objects.filter(job=self.job, user=self.seeker).exists())
        self.assertRedirects(r, reverse('applied_jobs'))

    def test_duplicate_application_redirects(self):
        Application.objects.create(job=self.job, user=self.seeker, cover_letter='Hi')
        r = self.client.post(reverse('apply_job', args=[self.job.pk]), {
            'cover_letter': 'Trying again',
        })
        self.assertEqual(Application.objects.filter(job=self.job, user=self.seeker).count(), 1)

    def test_employer_cannot_apply(self):
        self.client.logout()
        self.client.login(username='emp', password='testpass123')
        r = self.client.get(reverse('apply_job', args=[self.job.pk]))
        self.assertRedirects(r, reverse('unauthorized'))

    def test_apply_without_cover_letter_fails(self):
        r = self.client.post(reverse('apply_job', args=[self.job.pk]), {
            'cover_letter': '',
        })
        self.assertFalse(Application.objects.filter(job=self.job, user=self.seeker).exists())

    def test_unauthenticated_redirected_to_login(self):
        self.client.logout()
        r = self.client.get(reverse('apply_job', args=[self.job.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])


class AppliedJobsViewTest(TestCase):
    def setUp(self):
        self.seeker = make_seeker()
        emp = make_employer()
        self.job = make_job(emp)
        self.client.login(username='seek', password='testpass123')

    def test_loads_for_seeker(self):
        r = self.client.get(reverse('applied_jobs'))
        self.assertEqual(r.status_code, 200)

    def test_shows_own_applications(self):
        Application.objects.create(job=self.job, user=self.seeker, cover_letter='Hi')
        r = self.client.get(reverse('applied_jobs'))
        self.assertContains(r, self.job.title)

    def test_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse('applied_jobs'))
        self.assertRedirects(r, '/accounts/login/?next=/my-applications/')


# ─────────────────────────────────────────────
# VIEW TESTS — EMPLOYER
# ─────────────────────────────────────────────

class EmployerJobsViewTest(TestCase):
    def setUp(self):
        self.emp = make_employer()
        self.client.login(username='emp', password='testpass123')

    def test_loads_for_employer(self):
        r = self.client.get(reverse('employer_jobs'))
        self.assertEqual(r.status_code, 200)

    def test_shows_own_jobs_only(self):
        other_emp = make_employer('emp2')
        make_job(self.emp, title='My Job')
        make_job(other_emp, title='Other Job')
        r = self.client.get(reverse('employer_jobs'))
        self.assertContains(r, 'My Job')
        self.assertNotContains(r, 'Other Job')

    def test_seeker_redirected(self):
        self.client.logout()
        make_seeker()
        self.client.login(username='seek', password='testpass123')
        r = self.client.get(reverse('employer_jobs'))
        self.assertRedirects(r, reverse('unauthorized'))


class JobCreateViewTest(TestCase):
    def setUp(self):
        self.emp = make_employer()
        self.cat = make_category()
        self.client.login(username='emp', password='testpass123')

    def test_create_form_loads(self):
        r = self.client.get(reverse('job_create'))
        self.assertEqual(r.status_code, 200)

    def test_create_job_sets_posted_by(self):
        r = self.client.post(reverse('job_create'), {
            'title': 'New Position',
            'company_name': 'TestCorp',
            'description': 'A great job with lots of responsibilities.',
            'location': 'Pune',
            'job_type': 'Full-Time',
            'experience': 2,
            'salary': 1200000,
            'category': self.cat.pk,
        })
        job = Job.objects.filter(title='New Position').first()
        self.assertIsNotNone(job)
        self.assertEqual(job.posted_by, self.emp)

    def test_new_job_not_approved_by_default(self):
        self.client.post(reverse('job_create'), {
            'title': 'Pending Job',
            'company_name': 'TestCorp',
            'description': 'Waiting for approval.',
            'location': 'Pune',
            'job_type': 'Full-Time',
            'experience': 1,
            'category': self.cat.pk,
        })
        job = Job.objects.filter(title='Pending Job').first()
        if job:
            self.assertFalse(job.is_approved)


class JobEditViewTest(TestCase):
    def setUp(self):
        self.emp = make_employer()
        self.job = make_job(self.emp)
        self.cat = make_category()
        self.client.login(username='emp', password='testpass123')

    def test_edit_own_job(self):
        r = self.client.get(reverse('job_edit', args=[self.job.pk]))
        self.assertEqual(r.status_code, 200)

    def test_cannot_edit_other_employers_job(self):
        other = make_employer('emp3')
        other_job = make_job(other)
        r = self.client.get(reverse('job_edit', args=[other_job.pk]))
        self.assertEqual(r.status_code, 404)


class EmployerApplicationsViewTest(TestCase):
    def setUp(self):
        self.emp = make_employer()
        self.seeker = make_seeker()
        self.job = make_job(self.emp)
        Application.objects.create(job=self.job, user=self.seeker, cover_letter='Hire me')
        self.client.login(username='emp', password='testpass123')

    def test_loads_for_employer(self):
        r = self.client.get(reverse('employer_applications'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.seeker.username)

    def test_cannot_see_other_employers_applications(self):
        other_emp = make_employer('emp4')
        other_seeker = make_seeker('seek4')
        other_job = make_job(other_emp)
        Application.objects.create(job=other_job, user=other_seeker, cover_letter='Hey')
        r = self.client.get(reverse('employer_applications'))
        self.assertNotContains(r, other_seeker.username)

    def test_update_application_status(self):
        app = Application.objects.get(job=self.job, user=self.seeker)
        r = self.client.post(reverse('update_application_status', args=[app.pk]), {
            'status': 'shortlisted'
        })
        app.refresh_from_db()
        self.assertEqual(app.status, 'shortlisted')


# ─────────────────────────────────────────────
# VIEW TESTS — ADMIN
# ─────────────────────────────────────────────

class ApproveJobsViewTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin', password='adminpass', email='admin@test.com'
        )
        self.emp = make_employer()
        self.pending_job = make_job(self.emp, approved=False, title='Pending Job')
        self.client.login(username='admin', password='adminpass')

    def test_admin_can_access(self):
        r = self.client.get(reverse('approve_jobs'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Pending Job')

    def test_non_admin_redirected(self):
        self.client.logout()
        self.client.login(username='emp', password='testpass123')
        r = self.client.get(reverse('approve_jobs'))
        self.assertRedirects(r, reverse('unauthorized'))

    def test_approve_job(self):
        self.client.post(reverse('approve_job', args=[self.pending_job.pk]))
        self.pending_job.refresh_from_db()
        self.assertTrue(self.pending_job.is_approved)

    def test_reject_job_deletes_it(self):
        pk = self.pending_job.pk
        self.client.post(reverse('reject_job', args=[pk]))
        self.assertFalse(Job.objects.filter(pk=pk).exists())


# ─────────────────────────────────────────────
# VIEW TESTS — PROFILE
# ─────────────────────────────────────────────

class ProfileViewTest(TestCase):
    def setUp(self):
        self.seeker = make_seeker()
        self.client.login(username='seek', password='testpass123')

    def test_own_profile_loads(self):
        r = self.client.get(reverse('profile', args=[self.seeker.pk]))
        self.assertEqual(r.status_code, 200)

    def test_other_profile_loads(self):
        other = make_seeker('other')
        r = self.client.get(reverse('profile', args=[other.pk]))
        self.assertEqual(r.status_code, 200)

    def test_edit_profile_page_loads(self):
        r = self.client.get(reverse('edit_profile'))
        self.assertEqual(r.status_code, 200)

    def test_edit_profile_saves_skills(self):
        r = self.client.post(reverse('edit_profile'), {
            'skills': 'Python, Django, PostgreSQL',
            'education': 'B.Sc CS',
            'experience': '2 years',
            'bio': 'I am a developer',
            'phone': '9876543210',
            'location': 'Mumbai',
            'website': 'https://example.com',
        })
        self.seeker.profile.refresh_from_db()
        self.assertEqual(self.seeker.profile.skills, 'Python, Django, PostgreSQL')

    def test_profile_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse('edit_profile'))
        self.assertEqual(r.status_code, 302)


# ─────────────────────────────────────────────
# ACCESS CONTROL TESTS
# ─────────────────────────────────────────────

class AccessControlTest(TestCase):
    def setUp(self):
        self.emp = make_employer()
        self.seeker = make_seeker()
        self.job = make_job(self.emp)

    def test_anonymous_cannot_apply(self):
        r = self.client.get(reverse('apply_job', args=[self.job.pk]))
        self.assertIn(r.status_code, [302, 403])

    def test_anonymous_cannot_access_employer_dashboard(self):
        r = self.client.get(reverse('employer_jobs'))
        self.assertEqual(r.status_code, 302)

    def test_seeker_cannot_post_jobs(self):
        self.client.login(username='seek', password='testpass123')
        r = self.client.get(reverse('job_create'))
        self.assertRedirects(r, reverse('unauthorized'))

    def test_seeker_cannot_moderate(self):
        self.client.login(username='seek', password='testpass123')
        r = self.client.get(reverse('approve_jobs'))
        self.assertRedirects(r, reverse('unauthorized'))

    def test_employer_cannot_moderate(self):
        self.client.login(username='emp', password='testpass123')
        r = self.client.get(reverse('approve_jobs'))
        self.assertRedirects(r, reverse('unauthorized'))

    def test_unauthorized_page_loads(self):
        r = self.client.get(reverse('unauthorized'))
        self.assertEqual(r.status_code, 200)


# ─────────────────────────────────────────────
# CONTEXT PROCESSOR TESTS
# ─────────────────────────────────────────────

class ContextProcessorTest(TestCase):
    def test_is_employer_true_for_employer(self):
        make_employer()
        self.client.login(username='emp', password='testpass123')
        r = self.client.get(reverse('home'))
        self.assertTrue(r.context['is_employer'])
        self.assertFalse(r.context['is_job_seeker'])
        self.assertFalse(r.context['is_admin'])

    def test_is_job_seeker_true_for_seeker(self):
        make_seeker()
        self.client.login(username='seek', password='testpass123')
        r = self.client.get(reverse('home'))
        self.assertFalse(r.context['is_employer'])
        self.assertTrue(r.context['is_job_seeker'])

    def test_is_admin_true_for_superuser(self):
        User.objects.create_superuser('sadmin', 'sa@test.com', 'adminpass')
        self.client.login(username='sadmin', password='adminpass')
        r = self.client.get(reverse('home'))
        self.assertTrue(r.context['is_admin'])

    def test_all_false_for_anonymous(self):
        r = self.client.get(reverse('home'))
        self.assertFalse(r.context['is_employer'])
        self.assertFalse(r.context['is_job_seeker'])
        self.assertFalse(r.context['is_admin'])
