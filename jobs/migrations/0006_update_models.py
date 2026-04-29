from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0005_alter_profile_role'),
    ]

    operations = [
        # Make salary optional on Job
        migrations.AlterField(
            model_name='job',
            name='salary',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True),
        ),
        # Make category optional on Job
        migrations.AlterField(
            model_name='job',
            name='category',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='jobs.category'
            ),
        ),
        # Add status to Application
        migrations.AddField(
            model_name='application',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('reviewed', 'Reviewed'),
                    ('shortlisted', 'Shortlisted'),
                    ('rejected', 'Rejected'),
                ],
                default='pending', max_length=20
            ),
        ),
        # Add unique_together to Application
        migrations.AlterUniqueTogether(
            name='application',
            unique_together={('job', 'user')},
        ),
        # Add new profile fields
        migrations.AddField(
            model_name='profile',
            name='bio',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='phone',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='profile',
            name='location',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='profile',
            name='website',
            field=models.URLField(blank=True),
        ),
    ]
