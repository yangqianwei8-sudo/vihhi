# Generated manually to add position field to ContactColleague model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0041_add_contact_colleague'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactcolleague',
            name='position',
            field=models.CharField(blank=True, max_length=100, verbose_name='职位'),
        ),
    ]

