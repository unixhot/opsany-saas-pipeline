from django.db import migrations


def run_init(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pipeline', '0003_init_sync_jenkins_data_cron_task'),
    ]

    operations = [
        migrations.RunPython(run_init)
    ]
