# Generated by Django 2.1.7 on 2019-03-07 03:23

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


forward = """
    CREATE TABLE catmaid_group_inactivity_period (
        id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
        max_inactivity interval NOT NULL,
        message text,
        comment text,
        group_id int REFERENCES auth_group(id) ON DELETE CASCADE
    );

    CREATE TABLE catmaid_group_inactivity_period_contact (
        id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
        inactivity_period_id int REFERENCES catmaid_group_inactivity_period(id) ON DELETE CASCADE,
        user_id int REFERENCES auth_user ON DELETE CASCADE
    );

    SELECT create_history_table('catmaid_group_inactivity_period'::regclass);
    SELECT create_history_table('catmaid_group_inactivity_period_contact'::regclass);
"""


backward = """
    SELECT drop_history_table('catmaid_group_inactivity_period'::regclass);
    SELECT drop_history_table('catmaid_group_inactivity_period_contact'::regclass);

    DROP TABLE catmaid_group_inactivity_period_contact;
    DROP TABLE catmaid_group_inactivity_period;
"""


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0009_alter_user_last_name_max_length'),
        ('catmaid', '0066_update_volume_geometry_field_type'),
    ]

    operations = [
        migrations.RunSQL(
            forward,
            backward,
            [
                migrations.CreateModel(
                    name='GroupInactivityPeriod',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('max_inactivity', models.DurationField(default=datetime.timedelta(365), help_text='The time after which a user of the linked groups should be marked inactive.')),
                        ('message', models.TextField(blank=True, help_text='An optional message that is shown instead of the default text in the front-end.', null=True)),
                        ('comment', models.TextField(blank=True, help_text='An optional internal comment. It is displayed nowhere.', null=True)),
                        ('group', models.ForeignKey(help_text='This inactivity period applies to users of this group.', on_delete=django.db.models.deletion.DO_NOTHING, to='auth.Group')),
                    ],
                    options={
                        'db_table': 'catmaid_group_inactivity_period',
                    },
                ),
                migrations.CreateModel(
                    name='GroupInactivityPeriodContact',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('inactivity_period', models.ForeignKey(help_text='The inactivity period the linked user should act as contact person for.', on_delete=django.db.models.deletion.DO_NOTHING, to='catmaid.GroupInactivityPeriod')),
                        ('user', models.ForeignKey(help_text='The cantact person for the linked inactivity group.', on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'catmaid_group_inactivity_period_contact',
                    },
                ),
            ]),
    ]
