from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    """The columns match_sample and random_sample of the nblastconfig table can
    be null and empty. This is already reflected in the database, just not in
    the Django models, which is why NoOps are used for the actual forward and
    backward migration.

    Update: this has been fixed in the original migration since, and therefore
    this migration become effectively a complete NoOp.
    """

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catmaid', '0073_make_skeleton_summary_update_more_modular'),
    ]

    operations = [
        migrations.RunSQL(migrations.RunSQL.noop, migrations.RunSQL.noop),
    ]
