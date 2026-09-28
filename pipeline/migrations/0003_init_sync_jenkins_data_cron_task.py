from django.db import migrations


def run_init(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pipeline', '0002_create_default_number_script'),
    ]

    operations = [
        migrations.RunPython(run_init)
    ]
