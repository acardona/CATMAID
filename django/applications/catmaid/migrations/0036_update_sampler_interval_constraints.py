# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-04-04 23:24

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catmaid', '0035_add_skeleton_summary_table'),
    ]

    operations = [

        migrations.AlterField(
            model_name='samplerinterval',
            name='end_node',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='sampler_interval_end_node_set', to='catmaid.Treenode'),
        ),
        migrations.AlterField(
            model_name='samplerinterval',
            name='start_node',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='sampler_interval_start_node_set', to='catmaid.Treenode'),
        ),

    ]
