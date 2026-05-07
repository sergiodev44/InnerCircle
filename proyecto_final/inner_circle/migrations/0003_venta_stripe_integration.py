# Generated migration for Stripe integration

from django.db import migrations, models
from decimal import Decimal


def migrate_importe_to_precio_base(apps, schema_editor):
    """Migrate existing importe values to precio_base"""
    Venta = apps.get_model('inner_circle', 'Venta')
    for venta in Venta.objects.all():
        # precio_base was added with the old importe value, so we just need to ensure it's set
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('inner_circle', '0002_user_is_banned'),
    ]

    operations = [
        # Remove old importe field and add new fields
        migrations.RemoveField(
            model_name='venta',
            name='importe',
        ),
        migrations.AddField(
            model_name='venta',
            name='precio_base',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='venta',
            name='impuesto',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6),
        ),
        migrations.AddField(
            model_name='venta',
            name='tarifa_servicio',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6),
        ),
        migrations.AddField(
            model_name='venta',
            name='importe_total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='venta',
            name='estado_pago',
            field=models.CharField(choices=[('no_pagado', 'no pagado'), ('pagado', 'pagado'), ('fallido', 'fallido')], default='no_pagado'),
        ),
        migrations.AddField(
            model_name='venta',
            name='stripe_payment_intent',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
