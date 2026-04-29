"""
Management command to seed the database with sample data.
Run: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from jobs.models import Category, Job, Profile


CATEGORIES = [
    "Software Development", "Data Science & AI", "Design & UX",
    "Marketing", "Sales", "Finance & Accounting",
    "Human Resources", "Customer Support", "DevOps & Cloud", "Product Management",
]

SAMPLE_JOBS = [
    {
        "title": "Senior Django Developer",
        "company": "TechCorp India",
        "location": "Bengaluru, Karnataka",
        "description": (
            "We are looking for an experienced Django developer to join our team.\n\n"
            "Responsibilities:\n"
            "- Design and build scalable REST APIs\n"
            "- Work with PostgreSQL and Redis\n"
            "- Mentor junior developers\n"
            "- Participate in code reviews\n\n"
            "Requirements:\n"
            "- 4+ years of Django experience\n"
            "- Strong Python skills\n"
            "- Experience with Docker and CI/CD\n"
            "- Good communication skills"
        ),
        "salary": 1800000,
        "job_type": "Full-Time",
        "experience": 4,
        "category": "Software Development",
    },
    {
        "title": "React Frontend Engineer",
        "company": "PixelWave Studios",
        "location": "Mumbai, Maharashtra",
        "description": (
            "Join our creative team as a React Frontend Engineer.\n\n"
            "Responsibilities:\n"
            "- Build pixel-perfect UIs from Figma designs\n"
            "- Optimize app performance\n"
            "- Collaborate with backend engineers\n\n"
            "Requirements:\n"
            "- 3+ years React experience\n"
            "- Proficiency in TypeScript\n"
            "- Experience with Redux or Zustand\n"
            "- Eye for design and detail"
        ),
        "salary": 1400000,
        "job_type": "Full-Time",
        "experience": 3,
        "category": "Software Development",
    },
    {
        "title": "Data Scientist",
        "company": "DataMinds Analytics",
        "location": "Hyderabad, Telangana",
        "description": (
            "We need a skilled Data Scientist to extract insights from large datasets.\n\n"
            "Responsibilities:\n"
            "- Build predictive ML models\n"
            "- Analyze customer behaviour data\n"
            "- Present findings to stakeholders\n\n"
            "Requirements:\n"
            "- 2+ years in data science\n"
            "- Python (pandas, scikit-learn, PyTorch)\n"
            "- SQL proficiency\n"
            "- Strong statistics background"
        ),
        "salary": 1600000,
        "job_type": "Full-Time",
        "experience": 2,
        "category": "Data Science & AI",
    },
    {
        "title": "UI/UX Designer",
        "company": "CreativeHub",
        "location": "Pune, Maharashtra",
        "description": (
            "We're looking for a talented UI/UX Designer.\n\n"
            "Responsibilities:\n"
            "- Design intuitive user interfaces in Figma\n"
            "- Conduct user research and usability testing\n"
            "- Create wireframes, prototypes, and design systems\n\n"
            "Requirements:\n"
            "- 2+ years UI/UX experience\n"
            "- Proficiency in Figma and Adobe XD\n"
            "- Portfolio of shipped products\n"
            "- Understanding of accessibility standards"
        ),
        "salary": 1100000,
        "job_type": "Full-Time",
        "experience": 2,
        "category": "Design & UX",
    },
    {
        "title": "DevOps Engineer",
        "company": "CloudNine Technologies",
        "location": "Remote",
        "description": (
            "Join our infrastructure team as a DevOps Engineer.\n\n"
            "Responsibilities:\n"
            "- Manage AWS infrastructure using Terraform\n"
            "- Build and maintain CI/CD pipelines\n"
            "- Monitor and improve system reliability\n\n"
            "Requirements:\n"
            "- 3+ years DevOps/SRE experience\n"
            "- Kubernetes and Docker expertise\n"
            "- Familiarity with GitHub Actions or Jenkins\n"
            "- AWS/GCP certification a plus"
        ),
        "salary": 2000000,
        "job_type": "Remote",
        "experience": 3,
        "category": "DevOps & Cloud",
    },
    {
        "title": "Product Manager",
        "company": "StartupXYZ",
        "location": "Delhi NCR",
        "description": (
            "Shape the product roadmap as our first PM hire.\n\n"
            "Responsibilities:\n"
            "- Define product vision and strategy\n"
            "- Work closely with engineering and design\n"
            "- Gather and prioritize user requirements\n"
            "- Track KPIs and iterate\n\n"
            "Requirements:\n"
            "- 3+ years product management experience\n"
            "- Strong analytical mindset\n"
            "- Excellent communication skills\n"
            "- Technical background preferred"
        ),
        "salary": 2200000,
        "job_type": "Full-Time",
        "experience": 3,
        "category": "Product Management",
    },
    {
        "title": "Python Backend Intern",
        "company": "GreenTech Solutions",
        "location": "Chennai, Tamil Nadu",
        "description": (
            "Great opportunity for students or fresh graduates.\n\n"
            "Responsibilities:\n"
            "- Assist in building backend APIs\n"
            "- Write unit tests\n"
            "- Fix bugs and improve documentation\n\n"
            "Requirements:\n"
            "- Basic Python and Django knowledge\n"
            "- Understanding of REST APIs\n"
            "- Eagerness to learn\n"
            "- Pursuing or completed CS degree"
        ),
        "salary": 300000,
        "job_type": "Internship",
        "experience": 0,
        "category": "Software Development",
    },
    {
        "title": "Digital Marketing Manager",
        "company": "BrandBoost Agency",
        "location": "Mumbai, Maharashtra",
        "description": (
            "Lead our digital marketing efforts.\n\n"
            "Responsibilities:\n"
            "- Plan and execute SEO/SEM campaigns\n"
            "- Manage social media presence\n"
            "- Analyse campaign performance\n"
            "- Work with content team\n\n"
            "Requirements:\n"
            "- 3+ years digital marketing experience\n"
            "- Google Ads and Analytics certified\n"
            "- Strong copywriting skills\n"
            "- Data-driven mindset"
        ),
        "salary": 900000,
        "job_type": "Full-Time",
        "experience": 3,
        "category": "Marketing",
    },
]


class Command(BaseCommand):
    help = "Seeds the database with sample categories, jobs, and demo users."

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write("Clearing existing data…")
            Job.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        # ── Categories ──
        self.stdout.write("Creating categories…")
        cat_map = {}
        for name in CATEGORIES:
            cat, _ = Category.objects.get_or_create(name=name)
            cat_map[name] = cat
        self.stdout.write(self.style.SUCCESS(f"  ✔ {len(CATEGORIES)} categories ready"))

        # ── Demo employer ──
        if not User.objects.filter(username='employer_demo').exists():
            emp_user = User.objects.create_user(
                username='employer_demo',
                email='employer@demo.com',
                password='demo1234',
                first_name='Demo',
                last_name='Employer',
            )
            emp_user._profile_role = 'employer'
            emp_user.save()
            if hasattr(emp_user, 'profile'):
                emp_user.profile.role = 'employer'
                emp_user.profile.save()
            self.stdout.write(self.style.SUCCESS("  ✔ Employer demo: employer_demo / demo1234"))
        else:
            emp_user = User.objects.get(username='employer_demo')

        # ── Demo job seeker ──
        if not User.objects.filter(username='seeker_demo').exists():
            seek_user = User.objects.create_user(
                username='seeker_demo',
                email='seeker@demo.com',
                password='demo1234',
                first_name='Demo',
                last_name='Seeker',
            )
            if hasattr(seek_user, 'profile'):
                seek_user.profile.skills = 'Python, Django, JavaScript, SQL, Git'
                seek_user.profile.education = 'B.Sc Computer Science, Mumbai University (2020–2024)'
                seek_user.profile.experience = 'Junior Developer at StartupABC (2024–Present)'
                seek_user.profile.bio = 'Passionate developer looking for exciting opportunities.'
                seek_user.profile.location = 'Mumbai, Maharashtra'
                seek_user.profile.save()
            self.stdout.write(self.style.SUCCESS("  ✔ Job seeker demo: seeker_demo / demo1234"))

        # ── Sample jobs ──
        self.stdout.write("Creating sample jobs…")
        created = 0
        for jd in SAMPLE_JOBS:
            if not Job.objects.filter(title=jd['title'], company_name=jd['company']).exists():
                Job.objects.create(
                    title=jd['title'],
                    company_name=jd['company'],
                    location=jd['location'],
                    description=jd['description'],
                    salary=jd['salary'],
                    job_type=jd['job_type'],
                    experience=jd['experience'],
                    category=cat_map.get(jd['category']),
                    posted_by=emp_user,
                    is_approved=True,
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f"  ✔ {created} jobs created"))

        self.stdout.write(self.style.SUCCESS("\n✅ Seed complete! Run: python manage.py runserver"))
        self.stdout.write("   Admin: python manage.py createsuperuser")
        self.stdout.write("   Demo login → employer_demo / demo1234  |  seeker_demo / demo1234")
