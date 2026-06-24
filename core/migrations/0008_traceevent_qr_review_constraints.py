# Generated for trace QR code and trace-event integrity support.

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0007_add_review_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='productbatch',
            name='qr_code',
            field=models.ImageField(blank=True, help_text='溯源二维码', null=True, upload_to='qrcodes/'),
        ),
        migrations.AlterField(
            model_name='review',
            name='rating',
            field=models.PositiveSmallIntegerField(
                default=5,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(5),
                ],
            ),
        ),
        migrations.CreateModel(
            name='TraceEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('planting', '种植'), ('fertilizing', '施肥'), ('pesticide', '农药'), ('harvest', '采收'), ('qc', '质检'), ('storage', '入库'), ('shipping', '发货'), ('other', '其他')], default='other', max_length=30)),
                ('title', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True)),
                ('occurred_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('location', models.CharField(blank=True, max_length=200)),
                ('previous_hash', models.CharField(blank=True, max_length=64)),
                ('data_hash', models.CharField(blank=True, db_index=True, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='core.productbatch')),
                ('operator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['occurred_at', 'created_at'],
            },
        ),
    ]
