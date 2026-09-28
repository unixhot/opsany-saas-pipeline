from django.db import migrations

from pipeline.utils.init_script import run


def run_init(apps, schema_editor):
    run()


class Migration(migrations.Migration):

    dependencies = [
        ('pipeline', '0001_init_job'),
    ]

    operations = [
        migrations.RunPython(run_init)
    ]
