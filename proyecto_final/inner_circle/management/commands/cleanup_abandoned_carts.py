from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from inner_circle.models import Venta, Product

class Command(BaseCommand):
    help = 'Release products from abandoned carts (unpaid for >15 minutes)'

    def handle(self, *args, **options):
        cutoff_time = timezone.now() - timedelta(minutes=15)
        
        # Find abandoned Ventas: unpaid, created >15 min ago
        abandoned = Venta.objects.filter(
            estado_pago='no_pagado',
            created_at__lt=cutoff_time
        )
        
        count = 0
        for venta in abandoned:
            product = venta.product
            if product.estado == 'RESV':
                product.estado = 'DISP'
                product.save()
                venta.estado_pago = 'cancelada'
                venta.save()
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ Released {count} products from abandoned carts'))
