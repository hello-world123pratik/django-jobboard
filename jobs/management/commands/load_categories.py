# jobs/management/commands/load_categories.py
from django.core.management.base import BaseCommand
from jobs.models import Category

class Command(BaseCommand):
    help = 'Load default job categories'

    def handle(self, *args, **options):
        categories = [
            "Software Development",
            "Data Science",
            "AI / Machine Learning",
            "Web Development",
            "Mobile App Development",
            "Cybersecurity",
            "Network Engineering",
            "Cloud Computing",
            "Project Management",
            "Product Management",
            "UI/UX Design",
            "Graphic Design",
            "Digital Marketing",
            "Content Writing",
            "Sales & Business Development",
            "Customer Support",
            "Human Resources (HR)",
            "Accounting & Finance",
            "Operations",
            "Legal",
            "Education / Training",
            "Healthcare / Medical",
            "Engineering (Civil / Mechanical / Electrical)",
            "Logistics & Supply Chain",
            "Internships",
            "Remote / Work from Home"
        ]

        for name in categories:
            Category.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS('✅ Categories loaded successfully.'))
