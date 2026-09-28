from django.db import migrations


from pipeline.utils.init_script import init_jenkins_sync_data_cron_task


def run_init(apps, schema_editor):
    # 增加定时任务（每间隔5分钟同步Jenkins任务）
    init_jenkins_sync_data_cron_task()


class Migration(migrations.Migration):

    dependencies = [
        ('pipeline', '0004_init_sync_jenkins_data_cron_task'),
    ]

    operations = [
        migrations.RunPython(run_init)
    ]
