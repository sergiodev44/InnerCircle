from django.core.management.base import BaseCommand
from inner_circle.models import User, Profile, Product, FriendRequest, Category, Conversation, Mensaje, Venta, Resena, Notification, ProductImage
from django.core.files.base import ContentFile
from django.utils import timezone
import os
import shutil
from pathlib import Path
from PIL import Image
from io import BytesIO

# Register HEIC support
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


class Command(BaseCommand):
    help = 'Populate database with Hemingway-inspired test data and product images'

    def handle(self, *args, **options):
        # Clear existing data (order matters due to foreign key constraints)
        ProductImage.objects.all().delete()
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
            'jerseis': Category.objects.create(nombre='Jerseis', descripcion='Jerseis y prendas de punto'),
        }

        # Copy AI PFPs to profiles folder if they don't exist
        ai_pfps_dir = Path('/home/sergio/Desktop/InnerCircle/proyecto_final/media/ai_pfps')
        profiles_dir = Path('/home/sergio/Desktop/InnerCircle/proyecto_final/media/profiles')
        
        if ai_pfps_dir.exists():
            for pfp_file in ai_pfps_dir.glob('*.png'):
                dest_file = profiles_dir / pfp_file.name
                if not dest_file.exists():
                    shutil.copy2(pfp_file, dest_file)

        # Hemingway character users with creative descriptions
        users_data = [
            {'username': 'santiago', 'email': 'santiago@test.com', 'mobile': 111111111, 'tag': 'Santiago', 
             'bio': '⛵ Weathered and wise. Selling authentic, timeless pieces. Like the sea, minimal and powerful.', 'pfp': 'male_ai_pfp_1.png'},
            {'username': 'robert', 'email': 'robert@test.com', 'mobile': 222222222, 'tag': 'Robert', 
             'bio': '🌅 Every garment tells a story. Clean lines, pure style. Life gives you second chances.', 'pfp': 'male_ai_pfp_2.png'},
            {'username': 'harry', 'email': 'harry@test.com', 'mobile': 333333333, 'tag': 'Harry', 
             'bio': '❄️ Scaling new heights with every collection. Premium pieces for the journey.', 'pfp': 'male_ai_pfp_3.png'},
            {'username': 'brett', 'email': 'brett@test.com', 'mobile': 444444444, 'tag': 'Brett', 
             'bio': '🌹 For whom the bell tolls? For style seekers like you. Vintage finds daily!', 'pfp': 'female_ai_pfp_1.png'},
            {'username': 'maria', 'email': 'maria@test.com', 'mobile': 555555555, 'tag': 'Maria', 
             'bio': '✨ A clean well-lighted place to find fashion gems. Organized chaos, beautiful order.', 'pfp': 'female_ai_pfp_.png'},
        ]

        users = {}
        for user_info in users_data:
            user = User.objects.create_user(
                username=user_info['username'],
                password='hemingway1954',
                email=user_info['email'],
                mobile=user_info['mobile']
            )
            profile = Profile.objects.get(user=user)
            profile.nombre_tag = user_info['tag']
            profile.bio = user_info['bio']
            profile.img_perfil = f"profiles/{user_info['pfp']}"
            profile.save()
            users[user_info['username']] = user

        # Get all images from media/my_clothes
        clothes_dir = Path('/home/sergio/Desktop/InnerCircle/proyecto_final/media/my_clothes')
        
        # Group images by base name (without _f, _b suffix and extension)
        image_groups = {}
        if clothes_dir.exists():
            for image_file in sorted(clothes_dir.iterdir()):
                if image_file.is_file():
                    # Extract base name (e.g., "baggy_jeans" from "baggy_jeans_f.HEIC")
                    stem = image_file.stem  # Name without extension
                    
                    # Check if it ends with _f or _b
                    if stem.endswith('_f') or stem.endswith('_b'):
                        base_name = stem[:-2]  # Remove the _f or _b
                        view_type = 'front' if stem.endswith('_f') else 'back'
                    else:
                        base_name = stem
                        view_type = 'front'
                    
                    if base_name not in image_groups:
                        image_groups[base_name] = []
                    image_groups[base_name].append({
                        'path': image_file,
                        'view_type': view_type,
                        'filename': image_file.name
                    })

        # Product data mapping
        products_data = [
            {
                'user': 'santiago',
                'nombre': 'Baggy Jeans Vintage',
                'descripcion': 'Classic baggy jeans with a timeless appeal. Comfortable and durable, perfect for that effortless 90s look. Like Hemingway\'s prose - simple, powerful, unforgettable.',
                'estado': 'DISP',
                'precio': 45.00,
                'talla': 'M',
                'category': 'pantalones',
                'image_group': 'baggy_jeans'
            },
            {
                'user': 'robert',
                'nombre': 'Cashmere Touch Sweater',
                'descripcion': 'Luxurious cashmere-blend sweater for those chilly mornings. Soft as a whispered memory, elegant as the sunrise itself.',
                'estado': 'DISP',
                'precio': 65.00,
                'talla': 'L',
                'category': 'sudaderas',
                'image_group': 'cashmere'
            },
            {
                'user': 'harry',
                'nombre': 'Corduroy Peak Jacket',
                'descripcion': 'Timeless corduroy in earthy tones. Built to last through all seasons, like the mountain that inspired its name.',
                'estado': 'DISP',
                'precio': 75.00,
                'talla': 'L',
                'category': 'chaquetones',
                'image_group': 'corduroy'
            },
            {
                'user': 'brett',
                'nombre': 'Country Spirit Shirt',
                'descripcion': 'Rugged country shirt with character. Every stain tells a story. Feel the earth beneath your feet.',
                'estado': 'DISP',
                'precio': 38.00,
                'talla': 'M',
                'category': 'camisetas',
                'image_group': 'country_shirt'
            },
            {
                'user': 'maria',
                'nombre': 'Crop Top Essential',
                'descripcion': 'Clean, minimal crop top perfect for layering. Versatile, timeless, essential. One piece, infinite possibilities.',
                'estado': 'DISP',
                'precio': 22.00,
                'talla': 'S',
                'category': 'camisetas',
                'image_group': 'crop_top'
            },
            {
                'user': 'santiago',
                'nombre': 'Jersey Fitted Navy',
                'descripcion': 'Fitted navy jersey that flatters every silhouette. Smooth like a perfectly crafted sentence.',
                'estado': 'DISP',
                'precio': 28.00,
                'talla': 'M',
                'category': 'jerseis',
                'image_group': 'fit_jersey'
            },
            {
                'user': 'robert',
                'nombre': 'Graphic Statement Tee',
                'descripcion': 'Bold graphic design on premium cotton. Express yourself without saying a word. Let the shirt speak for you.',
                'estado': 'DISP',
                'precio': 24.00,
                'talla': 'L',
                'category': 'camisetas',
                'image_group': 'g_shirt'
            },
            {
                'user': 'harry',
                'nombre': 'Comfortable Hoodie',
                'descripcion': 'Warm, cozy hoodie for those moments when you need comfort. Like a good book on a cold night.',
                'estado': 'DISP',
                'precio': 55.00,
                'talla': 'XL',
                'category': 'sudaderas',
                'image_group': 'hoodie'
            },
            {
                'user': 'brett',
                'nombre': 'Black Jeans Premium',
                'descripcion': 'Perfectly faded black jeans. Worn in but not worn out. Every wear adds character.',
                'estado': 'DISP',
                'precio': 50.00,
                'talla': 'M',
                'category': 'pantalones',
                'image_group': 'jeans_black'
            },
            {
                'user': 'maria',
                'nombre': 'Grey Jeans Vintage',
                'descripcion': 'Soft grey wash with that lived-in feeling. Comfortable from day one. Like an old friend you just reconnected with.',
                'estado': 'DISP',
                'precio': 48.00,
                'talla': 'L',
                'category': 'pantalones',
                'image_group': 'jeans_grey'
            },
            {
                'user': 'santiago',
                'nombre': 'Jersey Cotton Organic',
                'descripcion': 'Pure organic cotton jersey. Breathable, sustainable, timeless. For the conscious dresser.',
                'estado': 'DISP',
                'precio': 35.00,
                'talla': 'M',
                'category': 'jerseis',
                'image_group': 'jersey_algodon'
            },
            {
                'user': 'robert',
                'nombre': 'Crop Jersey Modern',
                'descripcion': 'Contemporary cropped jersey perfect for modern styling. Short on length, big on impact.',
                'estado': 'DISP',
                'precio': 26.00,
                'talla': 'S',
                'category': 'camisetas',
                'image_group': 'jersey_crop'
            },
            {
                'user': 'harry',
                'nombre': 'Grey Jersey Comfort',
                'descripcion': 'Soft grey jersey that moves with you. No boundaries, just freedom.',
                'estado': 'DISP',
                'precio': 32.00,
                'talla': 'L',
                'category': 'jerseis',
                'image_group': 'jersey_grey'
            },
            {
                'user': 'brett',
                'nombre': 'Striped Jersey Classic',
                'descripcion': 'Timeless stripes in classic colors. Simple elegance that never goes out of style.',
                'estado': 'DISP',
                'precio': 30.00,
                'talla': 'M',
                'category': 'jerseis',
                'image_group': 'jersey_stripped'
            },
            {
                'user': 'maria',
                'nombre': 'Metal Band Shirt',
                'descripcion': 'Rock your style with this metal-inspired shirt. Edgy, authentic, unapologetic.',
                'estado': 'DISP',
                'precio': 27.00,
                'talla': 'M',
                'category': 'camisetas',
                'image_group': 'metal_shirt'
            },
            {
                'user': 'santiago',
                'nombre': 'Navy Jeans Heritage',
                'descripcion': 'Navy denim with heritage. Built to last generations. A wardrobe staple with soul.',
                'estado': 'DISP',
                'precio': 52.00,
                'talla': 'M',
                'category': 'pantalones',
                'image_group': 'n_jeans'
            },
            {
                'user': 'robert',
                'nombre': 'Polo Brown Elegance',
                'descripcion': 'Elegant brown polo for any occasion. From casual to refined, this does it all.',
                'estado': 'DISP',
                'precio': 40.00,
                'talla': 'L',
                'category': 'camisetas',
                'image_group': 'polo_brown'
            },
            {
                'user': 'harry',
                'nombre': 'Shirt Secondary Look',
                'descripcion': 'Versatile shirt perfect for layering or wearing alone. Your new favorite piece.',
                'estado': 'DISP',
                'precio': 36.00,
                'talla': 'L',
                'category': 'camisetas',
                'image_group': 'shirt2'
            },
        ]

        # Helper function to convert HEIC to JPEG if needed
        def convert_heic_to_jpeg_if_needed(image_path):
            """Convert HEIC to JPEG format, return converted image data or original if not HEIC"""
            if image_path.suffix.lower() == '.heic':
                try:
                    img = Image.open(image_path)
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = rgb_img
                    
                    # Save to BytesIO
                    output = BytesIO()
                    img.save(output, format='JPEG', quality=90)
                    output.seek(0)
                    return output, 'jpeg'
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Error converting {image_path.name}: {str(e)}'))
                    return None, None
            else:
                # Return the file as-is for non-HEIC formats
                with open(image_path, 'rb') as f:
                    return f.read(), image_path.suffix[1:].lower()

        # Create products with images
        products = {}
        product_key = 0
        
        for prod_info in products_data:
            product = Product.objects.create(
                user=users[prod_info['user']],
                category=categories[prod_info['category']],
                nombre=prod_info['nombre'],
                descripcion=prod_info['descripcion'],
                estado=prod_info['estado'],
                precio=prod_info['precio'],
                talla=prod_info['talla'],
            )
            products[product_key] = product
            
            # Add images for this product
            image_group_name = prod_info['image_group']
            if image_group_name in image_groups:
                order = 0
                # Sort with 'front' first, then 'back'
                sorted_images = sorted(
                    image_groups[image_group_name], 
                    key=lambda x: (0 if x['view_type'] == 'front' else 1, x['view_type'])
                )
                for img_info in sorted_images:
                    image_path = img_info['path']
                    
                    # Convert HEIC if needed
                    image_data, image_format = convert_heic_to_jpeg_if_needed(image_path)
                    
                    if image_data:
                        # Determine new filename
                        if isinstance(image_data, bytes):
                            # Already converted, use BytesIO
                            filename = f"{image_group_name}_{order}.jpg"
                        else:
                            # BytesIO object
                            ext = 'jpg' if image_format == 'jpeg' else image_format
                            filename = f"{image_group_name}_{order}.{ext}"
                        
                        # Create ProductImage
                        if isinstance(image_data, bytes):
                            product_img = ProductImage.objects.create(
                                product=product,
                                order=order,
                                image=ContentFile(image_data, name=filename)
                            )
                        else:
                            product_img = ProductImage.objects.create(
                                product=product,
                                order=order,
                                image=ContentFile(image_data.getvalue(), name=filename)
                            )
                        
                        order += 1
                        self.stdout.write(self.style.SUCCESS(f'✓ Added image to {product.nombre}'))
            
            product_key += 1

        # Create friendships
        users['santiago'].friends.add(users['robert'])
        users['santiago'].friends.add(users['harry'])
        users['robert'].friends.add(users['brett'])
        users['harry'].friends.add(users['maria'])

        # Create friend requests
        fr1 = FriendRequest.objects.create(
            sender=users['brett'],
            recibidor2=users['robert'],
            status='pendiente'
        )
        fr2 = FriendRequest.objects.create(
            sender=users['maria'],
            recibidor2=users['santiago'],
            status='aceptada'
        )

        # Create conversations and messages
        conv1 = Conversation.objects.create(
            producto=products[0],
            usuario1=users['santiago'],
            usuario2=users['robert']
        )
        Mensaje.objects.create(
            conversation=conv1,
            sender=users['robert'],
            contenido='Those baggy jeans are perfect! Are they still available?'
        )
        Mensaje.objects.create(
            conversation=conv1,
            sender=users['santiago'],
            contenido='Yes, they are. Worn but with lots of life left in them.'
        )
        Mensaje.objects.create(
            conversation=conv1,
            sender=users['robert'],
            contenido='I\'ll take them! Can you ship to Barcelona?'
        )

        conv2 = Conversation.objects.create(
            producto=products[2],
            usuario1=users['harry'],
            usuario2=users['brett']
        )
        Mensaje.objects.create(
            conversation=conv2,
            sender=users['brett'],
            contenido='Love the corduroy! That color is exactly what I\'ve been looking for.'
        )
        Mensaje.objects.create(
            conversation=conv2,
            sender=users['harry'],
            contenido='It\'s a great piece. Very warm for winter.'
        )

        # Create sales and reviews
        from decimal import Decimal
        import uuid
        
        venta1 = Venta.objects.create(
            comprador=users['robert'],
            vendedor=users['santiago'],
            product=products[0],
            precio_base=Decimal('45.00'),
            impuesto=Decimal('4.50'),
            tarifa_servicio=Decimal('2.25'),
            importe_total=Decimal('51.75'),
            estado_pago='pagado',
            stripe_payment_intent=f'pi_test_{uuid.uuid4().hex[:12]}'
        )
        products[0].estado = 'VEND'
        products[0].deleted_at = timezone.now()
        products[0].save()
        
        venta2 = Venta.objects.create(
            comprador=users['brett'],
            vendedor=users['harry'],
            product=products[2],
            precio_base=Decimal('75.00'),
            impuesto=Decimal('7.50'),
            tarifa_servicio=Decimal('3.75'),
            importe_total=Decimal('86.25'),
            estado_pago='pagado',
            stripe_payment_intent=f'pi_test_{uuid.uuid4().hex[:12]}'
        )
        products[2].estado = 'VEND'
        products[2].deleted_at = timezone.now()
        products[2].save()

        # Create reviews
        resena1 = Resena.objects.create(
            escritor=users['robert'],
            recibidor=users['santiago'],
            venta=venta1,
            contenido='Beautiful vintage jeans! Exactly as described. The seller is a true professional. Five stars!',
            puntuacion=5
        )
        resena2 = Resena.objects.create(
            escritor=users['brett'],
            recibidor=users['harry'],
            venta=venta2,
            contenido='Corduroy jacket is perfection. High quality, great fit. Would buy from again!',
            puntuacion=5
        )

        # Create notifications
        Notification.objects.create(
            user=users['santiago'],
            tipo='venta',
            contenido='Robert purchased your Baggy Jeans Vintage!',
            object_id=venta1.id
        )
        Notification.objects.create(
            user=users['harry'],
            tipo='venta',
            contenido='Brett purchased your Corduroy Peak Jacket!',
            object_id=venta2.id
        )

        self.stdout.write(self.style.SUCCESS('✓ Database populated successfully with Hemingway-inspired data!'))
