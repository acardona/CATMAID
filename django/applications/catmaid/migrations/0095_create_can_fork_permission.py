# Generated by Django 2.2.7 on 2019-11-19 00:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catmaid', '0094_add_imported_cable_length_stats_summary_column'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='project',
            options={'managed': True, 'permissions': (('can_administer', 'Can administer projects'), ('can_annotate', 'Can annotate projects'), ('can_browse', 'Can browse projects'), ('can_import', 'Can import into projects'), ('can_queue_compute_task', 'Can queue resource-intensive tasks'), ('can_annotate_with_token', 'Can annotate project using API token'), ('can_fork', 'Can create personal copies of projects (only stacks)'))},
        ),
    ]
