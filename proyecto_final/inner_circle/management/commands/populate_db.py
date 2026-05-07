from django.core.management.base import BaseCommand
from inner_circle.models import User, Profile, Product, FriendRequest, Category, Conversation, Mensaje, Venta, Resena, Notification, Dispute
from django.core.files.base import ContentFile
from django.utils import timezone
import os


class Command(BaseCommand): #Dispute/Refund system - Buyer says "fake product" or "never received". Currently no way to handle except admin intervention. Real apps have evidence submission, timers, auto-resolution.
    help = 'Populate database with comprehensive test data'

    def handle(self, *args, **options):
        # Clear existing data (order matters due to foreign key constraints)
        Product.objects.all_including_deleted().delete()
        Venta.objects.all().delete()
        Conversation.objects.all().delete()
        Profile.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()
        
        # Create categories
        categories = {
            'camisetas': Category.objects.create(nombre='Camisetas', descripcion='T-shirts y camisetas'),
            'pantalones': Category.objects.create(nombre='Pantalones', descripcion='Pantalones y jeans'),
            'sudaderas': Category.objects.create(nombre='Sudaderas', descripcion='Sudaderas y hoodies'),
            'chaquetones': Category.objects.create(nombre='Chaquetones', descripcion='Chaquetas y abrigos'),
        }

        # Create users
        users_data = [
            {'username': 'goku', 'email': 'goku@test.com', 'mobile': 111111111, 'tag': 'Goku', 'bio': '🔥 Warrior of friendship and power! Always looking to gather amazing pieces!', 'pfp': 'gohan.png'},
            {'username': 'vegeta', 'email': 'vegeta@test.com', 'mobile': 222222222, 'tag': 'Prince Vegeta', 'bio': '👑 Elite taste in fashion. Only the finest items accepted.', 'pfp': 'vegeta.png'},
            {'username': 'broly', 'email': 'broly@test.com', 'mobile': 333333333, 'tag': 'Broly', 'bio': '💪 Strongest warrior. Selling legendary pieces.', 'pfp': 'broly.png'},
            {'username': 'bardock', 'email': 'bardock@test.com', 'mobile': 444444444, 'tag': 'Bardock', 'bio': '🎯 Experience matters. Quality over quantity always.', 'pfp': 'bardock.png'},
            {'username': 'boo', 'email': 'boo@test.com', 'mobile': 555555555, 'tag': 'Majin Boo', 'bio': '😊 Fun and friendly! Love finding treasures in the marketplace!', 'pfp': 'boo_pfp.png'},
        ]

        users = {}
        for user_info in users_data:
            user = User.objects.create_user(
                username=user_info['username'],
                password='spaceone0',
                email=user_info['email'],
                mobile=user_info['mobile']
            )
            # Signal auto-creates profile, just update it
            profile = Profile.objects.get(user=user)
            profile.nombre_tag = user_info['tag']
            profile.bio = user_info['bio']
            profile.img_perfil = f"profiles/{user_info['pfp']}"
            profile.save()
            users[user_info['username']] = user

        # Create products with images
        products_data = [
            {
                'user': 'goku',
                'nombre': 'Classic White T-Shirt',
                'descripcion': 'Pure white cotton tee, perfect condition. Great for casual outings.',
                'estado': 'DISP',
                'precio': 12.99,
                'talla': 'M',
                'category': 'camisetas',
                'image': 'shirt.webp'
            },
            {
                'user': 'goku',
                'nombre': 'Blue Striped Shirt',
                'descripcion': 'Comfortable striped shirt, lightly worn. Perfect summer piece.',
                'estado': 'DISP',
                'precio': 18.50,
                'talla': 'L',
                'category': 'camisetas',
                'image': 'shirt2.webp'
            },
            {
                'user': 'vegeta',
                'nombre': 'Premium Blue Jeans',
                'descripcion': 'High-quality denim jeans, dark blue color. Barely worn.',
                'estado': 'DISP',
                'precio': 45.00,
                'talla': 'M',
                'category': 'pantalones',
                'image': 'jeans.webp'
            },
            {
                'user': 'vegeta',
                'nombre': 'Black Slim Fit Jeans',
                'descripcion': 'Elegant black jeans with perfect fit. Ideal for any occasion.',
                'estado': 'DISP',
                'precio': 42.99,
                'talla': 'L',
                'category': 'pantalones',
                'image': 'jeans3.webp'
            },
            {
                'user': 'broly',
                'nombre': 'Red Hoodie',
                'descripcion': 'Cozy red hoodie, warm and comfortable. Great for winter.',
                'estado': 'DISP',
                'precio': 35.00,
                'talla': 'XL',
                'category': 'sudaderas',
                'image': 'hoodie.jpg'
            },
            {
                'user': 'broly',
                'nombre': 'Grey Hoodie',
                'descripcion': 'Classic grey hoodie, versatile and comfortable. Perfect all-season piece.',
                'estado': 'DISP',
                'precio': 38.00,
                'talla': 'L',
                'category': 'sudaderas',
                'image': 'hoodie2.webp'
            },
            {
                'user': 'bardock',
                'nombre': 'Black Sweatpants',
                'descripcion': 'Comfortable black sweatpants for lounging. High quality fabric.',
                'estado': 'DISP',
                'precio': 28.99,
                'talla': 'M',
                'category': 'pantalones',
                'image': 'sweatpants.webp'
            },
            {
                'user': 'boo',
                'nombre': 'Graphic T-Shirt',
                'descripcion': 'Fun graphic tee with cool design. Excellent condition.',
                'estado': 'DISP',
                'precio': 16.99,
                'talla': 'S',
                'category': 'camisetas',
                'image': 'shirt3.webp'
            },
            {
                'user': 'boo',
                'nombre': 'Blue Hoodie',
                'descripcion': 'Royal blue hoodie, very comfortable and durable.',
                'estado': 'DISP',
                'precio': 39.99,
                'talla': 'M',
                'category': 'sudaderas',
                'image': 'hoodie2.webp'
            },
        ]

        products = {}
        product_key = 0
        for idx, prod_info in enumerate(products_data):
            product = Product.objects.create(
                user=users[prod_info['user']],
                category=categories[prod_info['category']],
                nombre=prod_info['nombre'],
                descripcion=prod_info['descripcion'],
                estado=prod_info['estado'],
                precio=prod_info['precio'],
                talla=prod_info['talla'],
                img_prod=f"products/{prod_info['image']}"
            )
            products[product_key] = product
            product_key += 1

        # Create friendships
        users['goku'].friends.add(users['vegeta'])
        users['goku'].friends.add(users['broly'])
        users['goku'].friends.add(users['bardock'])
        users['vegeta'].friends.add(users['broly'])
        users['broly'].friends.add(users['boo'])
        users['bardock'].friends.add(users['boo'])

        # Create friend requests
        fr1 = FriendRequest.objects.create(
            sender=users['boo'],
            recibidor2=users['vegeta'],
            status='pendiente'
        )
        fr2 = FriendRequest.objects.create(
            sender=users['bardock'],
            recibidor2=users['goku'],
            status='aceptada'
        )

        # Create conversations and messages
        conv1 = Conversation.objects.create(
            producto=products[0],
            usuario1=users['goku'],
            usuario2=users['vegeta']
        )
        Mensaje.objects.create(
            conversation=conv1,
            sender=users['vegeta'],
            contenido='Hi! Is this shirt still available?'
        )
        Mensaje.objects.create(
            conversation=conv1,
            sender=users['goku'],
            contenido='Yes! It is! Great condition too.'
        )
        Mensaje.objects.create(
            conversation=conv1,
            sender=users['vegeta'],
            contenido='Would you accept 11.99?'
        )

        conv2 = Conversation.objects.create(
            producto=products[2],
            usuario1=users['broly'],
            usuario2=users['boo']
        )
        Mensaje.objects.create(
            conversation=conv2,
            sender=users['boo'],
            contenido='Love these jeans! How many times have you worn them?'
        )
        Mensaje.objects.create(
            conversation=conv2,
            sender=users['broly'],
            contenido='Only twice, they are almost like new!'
        )

        # Create sales (ventas) and mark products as VEND with soft delete
        from decimal import Decimal
        import uuid
        
        venta1 = Venta.objects.create(
            comprador=users['vegeta'],
            vendedor=users['goku'],
            product=products[0],
            precio_base=Decimal('12.99'),
            impuesto=Decimal('1.30'),
            tarifa_servicio=Decimal('0.65'),
            importe_total=Decimal('14.94'),
            estado_pago='pagado',
            stripe_payment_intent=f'pi_test_{uuid.uuid4().hex[:12]}'
        )
        products[0].estado = 'VEND'
        products[0].deleted_at = timezone.now()
        products[0].save()
        
        venta2 = Venta.objects.create(
            comprador=users['boo'],
            vendedor=users['broly'],
            product=products[4],
            precio_base=Decimal('35.00'),
            impuesto=Decimal('3.50'),
            tarifa_servicio=Decimal('1.75'),
            importe_total=Decimal('40.25'),
            estado_pago='pagado',
            stripe_payment_intent=f'pi_test_{uuid.uuid4().hex[:12]}'
        )
        products[4].estado = 'VEND'
        products[4].deleted_at = timezone.now()
        products[4].save()
        
        venta3 = Venta.objects.create(
            comprador=users['bardock'],
            vendedor=users['vegeta'],
            product=products[2],
            precio_base=Decimal('45.00'),
            impuesto=Decimal('4.50'),
            tarifa_servicio=Decimal('2.25'),
            importe_total=Decimal('51.75'),
            estado_pago='pagado',
            stripe_payment_intent=f'pi_test_{uuid.uuid4().hex[:12]}'
        )
        products[2].estado = 'VEND'
        products[2].deleted_at = timezone.now()
        products[2].save()

        # Create reviews (reseñas)
        resena1 = Resena.objects.create(
            escritor=users['vegeta'],
            recibidor=users['goku'],
            venta=venta1,
            contenido='Perfect transaction! Item was exactly as described. Very professional seller.',
            puntuacion=5
        )
        resena2 = Resena.objects.create(
            escritor=users['boo'],
            recibidor=users['broly'],
            venta=venta2,
            contenido='Great hoodie and fast delivery! Highly recommended.',
            puntuacion=5
        )
        resena3 = Resena.objects.create(
            escritor=users['bardock'],
            recibidor=users['vegeta'],
            venta=venta3,
            contenido='Quality product, good communication. Would buy again!',
            puntuacion=4
        )

        # Create notifications
        Notification.objects.create(
            user=users['goku'],
            tipo='venta',
            contenido='Vegeta purchased your Classic White T-Shirt!',
            object_id=venta1.id
        )
        Notification.objects.create(
            user=users['broly'],
            tipo='venta',
            contenido='Boo purchased your Red Hoodie!',
            object_id=venta2.id
        )
        Notification.objects.create(
            user=users['vegeta'],
            tipo='resena',
            contenido='You received a new review from Goku!',
            leido=False
        )
        Notification.objects.create(
            user=users['boo'],
            tipo='amistad',
            contenido='Vegeta sent you a friend request!',
            object_id=fr1.id
        )
        Notification.objects.create(
            user=users['vegeta'],
            tipo='mensaje',
            contenido='New message from Goku',
            leido=False
        )

        # Create test dispute (buyer claiming issue with purchase)
        dispute = Dispute.objects.create(
            venta=venta1,
            comprador=venta1.comprador,
            vendedor=venta1.vendedor,
            razon='not_as_described',
            descripcion='La camiseta que recibí no es la que ordené. Es de diferente color.'
        )
        
        # Notification to seller that dispute was filed
        Notification.objects.create(
            user=venta1.vendedor,
            tipo='dispute',
            contenido=f'{venta1.comprador.username} abrió una reclamación: Producto no corresponde a descripción',
            object_id=dispute.id
        )

        # Create admin user
        admin = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com',
            mobile=999999999
        )
        # Signal auto-creates profile, just update it
        admin_profile = Profile.objects.get(user=admin)
        admin_profile.nombre_tag = 'Admin'
        admin_profile.bio = '🔧 System Administrator'
        admin_profile.img_perfil = 'profiles/vegeta.png'
        admin_profile.save()

        self.stdout.write(self.style.SUCCESS('\n✅ Database populated successfully!\n'))
        self.stdout.write(f'✅ Created 5 users: {", ".join([u["username"] for u in users_data])}')
        self.stdout.write(f'✅ Created admin user: admin (password: admin123)')
        self.stdout.write(f'✅ All users password: spaceone0')
        self.stdout.write(f'✅ Created {len(categories)} categories')
        self.stdout.write(f'✅ Created {len(products)} products with images')
        self.stdout.write(f'✅ Created friendships and friend requests')
        self.stdout.write(f'✅ Created conversations with messages')
        self.stdout.write(f'✅ Created 3 sales (ventas) with reviews')
        self.stdout.write(f'✅ Created notifications for testing')
        self.stdout.write(f'✅ Created 1 test dispute (vegeta vs goku)\n')
