from django.core.management.base import BaseCommand
from django.conf import settings
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
except Exception as e:
    print(f"WARNING: Failed to register pillow_heif: {e}")


class Command(BaseCommand):
    help = 'Populate database (Spanish names/descriptions)'

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
            'camisetas': Category.objects.create(nombre='Camisetas', descripcion='Camisetas y tops'),
            'pantalones': Category.objects.create(nombre='Pantalones', descripcion='Pantalones y jeans'),
            'sudaderas': Category.objects.create(nombre='Sudaderas', descripcion='Sudaderas y hoodies'),
            'chaquetones': Category.objects.create(nombre='Chaquetones', descripcion='Chaquetas y abrigos'),
            'jerseis': Category.objects.create(nombre='Jerseis', descripcion='Jerseis y prendas de punto'),
        }

        # Copy AI PFPs to profiles folder if they don't exist
        base_media = Path(settings.MEDIA_ROOT)
        ai_pfps_dir = base_media / 'ai_pfps'
        profiles_dir = base_media / 'profiles'
        
        if ai_pfps_dir.exists():
            for pfp_file in ai_pfps_dir.glob('*.png'):
                dest_file = profiles_dir / pfp_file.name
                if not dest_file.exists():
                    shutil.copy2(pfp_file, dest_file)

        # Spanish-named users with Spanish bios
        users_data = [
            {'username': 'santiago', 'email': 'santiago@test.com', 'mobile': 111111111, 'tag': 'Santiago', 
             'bio': '⛵ Auténtico y con historia. Vendo prendas con carácter y personalidad.', 'pfp': 'male_ai_pfp_1.png'},
            {'username': 'roberto', 'email': 'roberto@test.com', 'mobile': 222222222, 'tag': 'Roberto', 
             'bio': '🌅 Prendas con historia. Estilo simple y duradero.', 'pfp': 'male_ai_pfp_2.png'},
            {'username': 'andres', 'email': 'andres@test.com', 'mobile': 333333333, 'tag': 'Andrés', 
             'bio': '❄️ Calidad y tradición en cada prenda. Diseños atemporales.', 'pfp': 'male_ai_pfp_3.png'},
            {'username': 'beatriz', 'email': 'beatriz@test.com', 'mobile': 444444444, 'tag': 'Beatriz', 
             'bio': '🌹 Encuentra piezas únicas y con alma. Vintage cuidado y seleccionado.', 'pfp': 'female_ai_pfp_1.png'},
            {'username': 'maria', 'email': 'maria@test.com', 'mobile': 555555555, 'tag': 'María', 
             'bio': '✨ Prendas prácticas y versátiles. Ideal para el día a día.', 'pfp': 'female_ai_pfp_.png'},
        ]

        users = {}
        for user_info in users_data:
            user = User.objects.create_user(
                username=user_info['username'],
                password='innercircle123',
                email=user_info['email'],
                mobile=user_info['mobile']
            )
            profile = Profile.objects.get(user=user)
            profile.nombre_tag = user_info['tag']
            profile.bio = user_info['bio']
            profile.location = 'Jerez de la Frontera'
            profile.img_perfil = f"profiles/{user_info['pfp']}"
            profile.save()
            users[user_info['username']] = user

        # Get all images from media/my_clothes
        clothes_dir = base_media / 'my_clothes'
        
        # Group images by base name (without _f, _b suffix and extension)
        image_groups = {}
        self.stdout.write(f"Looking for images in: {clothes_dir}")
        self.stdout.write(f"Directory exists: {clothes_dir.exists()}")
        if clothes_dir.exists():
            files_found = list(clothes_dir.iterdir())
            self.stdout.write(f"Files found in my_clothes: {len(files_found)}")
            for image_file in sorted(clothes_dir.iterdir()):
                if image_file.is_file():
                    stem = image_file.stem
                    if stem.endswith('_f') or stem.endswith('_b'):
                        base_name = stem[:-2]
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
            self.stdout.write(f"Image groups found: {list(image_groups.keys())}")

        # Product data mapping (Spanish names & descriptions)
        products_data = [
            {
                'user': 'santiago',
                'nombre': 'Vaqueros Baggy Vintage',
                'descripcion': 'Vaqueros baggy con un look 90s clásico. Cómodos y resistentes, perfectos para un estilo desenfadado. Como la prosa de Hemingway - simple, poderosa, inolvidable.',
                'estado': 'DISP',
                'precio': 45.00,
                'talla': 'M',
                'category': 'pantalones',
                'image_group': 'baggy_jeans'
            },
            {
                'user': 'roberto',
                'nombre': 'Jersey de Cashmira Suave',
                'descripcion': 'Jersey lujo con mezcla de cashmira para las mañanas frías. Suave como un recuerdo susurrado, elegante como el amanecer mismo.',
                'estado': 'DISP',
                'precio': 65.00,
                'talla': 'L',
                'category': 'sudaderas',
                'image_group': 'cashmere'
            },
            {
                'user': 'andres',
                'nombre': 'Chaqueta de Pana',
                'descripcion': 'Pana atemporal en tonos tierra. Construida para durar todas las estaciones, como la montaña que inspiró su nombre.',
                'estado': 'DISP',
                'precio': 75.00,
                'talla': 'L',
                'category': 'chaquetones',
                'image_group': 'corduroy'
            },
            {
                'user': 'beatriz',
                'nombre': 'Camisa Country con Carácter',
                'descripcion': 'Camisa country rugosa y con textura. Cada mancha cuenta una historia. Siente la tierra bajo tus pies.',
                'estado': 'DISP',
                'precio': 38.00,
                'talla': 'M',
                'category': 'camisetas',
                'image_group': 'country_shirt'
            },
            {
                'user': 'maria',
                'nombre': 'Top Crop Esencial',
                'descripcion': 'Top corto y minimalista, perfecto para capas. Versátil, atemporal, esencial. Una prenda, infinitas posibilidades.',
                'estado': 'DISP',
                'precio': 22.00,
                'talla': 'S',
                'category': 'camisetas',
                'image_group': 'crop_top'
            },
            {
                'user': 'santiago',
                'nombre': 'Jersey Azul Marino Ajustado',
                'descripcion': 'Jersey azul marino ajustado que favorece cualquier silueta. Suave como una frase perfectamente elaborada.',
                'estado': 'DISP',
                'precio': 28.00,
                'talla': 'M',
                'category': 'jerseis',
                'image_group': 'fit_jersey'
            },
            {
                'user': 'roberto',
                'nombre': 'Camiseta Gráfica Impactante',
                'descripcion': 'Diseño gráfico audaz en algodón premium. Exprésate sin decir una palabra. Deja que la camiseta hable por ti.',
                'estado': 'DISP',
                'precio': 24.00,
                'talla': 'L',
                'category': 'camisetas',
                'image_group': 'g_shirt'
            },
            {
                'user': 'andres',
                'nombre': 'Sudadera Cómoda',
                'descripcion': 'Sudadera cálida y acogedora para esos momentos en que necesitas confort. Como un buen libro en una noche fría.',
                'estado': 'DISP',
                'precio': 55.00,
                'talla': 'XL',
                'category': 'sudaderas',
                'image_group': 'hoodie'
            },
            {
                'user': 'beatriz',
                'nombre': 'Vaqueros Negros Premium',
                'descripcion': 'Vaqueros negros perfectamente desteñidos. Gastados pero no rotos. Cada uso añade carácter.',
                'estado': 'DISP',
                'precio': 50.00,
                'talla': 'M',
                'category': 'pantalones',
                'image_group': 'jeans_black'
            },
            {
                'user': 'maria',
                'nombre': 'Vaqueros Grises Vintage',
                'descripcion': 'Lavado gris suave con ese aspecto gastado. Cómodos desde el primer día. Como un viejo amigo con el que acabas de reconectarte.',
                'estado': 'DISP',
                'precio': 48.00,
                'talla': 'L',
                'category': 'pantalones',
                'image_group': 'jeans_grey'
            },
            {
                'user': 'santiago',
                'nombre': 'Jersey Algodón Orgánico',
                'descripcion': 'Jersey 100% algodón orgánico. Transpirable, sostenible, atemporal. Para el que compra conscientemente.',
                'estado': 'DISP',
                'precio': 35.00,
                'talla': 'M',
                'category': 'jerseis',
                'image_group': 'jersey_algodon'
            },
            {
                'user': 'roberto',
                'nombre': 'Jersey Crop Moderno',
                'descripcion': 'Jersey cropped contemporáneo perfecto para estilos modernos. Corto en largo, grande en impacto.',
                'estado': 'DISP',
                'precio': 26.00,
                'talla': 'S',
                'category': 'camisetas',
                'image_group': 'jersey_crop'
            },
            {
                'user': 'andres',
                'nombre': 'Jersey Gris Cómodo',
                'descripcion': 'Jersey gris suave que se adapta a ti. Sin límites, solo libertad.',
                'estado': 'DISP',
                'precio': 32.00,
                'talla': 'L',
                'category': 'jerseis',
                'image_group': 'jeans_grey'
            },
            {
                'user': 'beatriz',
                'nombre': 'Jersey Rayas Clásicas',
                'descripcion': 'Rayas atemporales en colores clásicos. Elegancia simple que nunca pasa de moda.',
                'estado': 'DISP',
                'precio': 30.00,
                'talla': 'M',
                'category': 'jerseis',
                'image_group': 'jersey_stripped'
            },
            {
                'user': 'maria',
                'nombre': 'Camiseta Metal Rock',
                'descripcion': 'Viste tu estilo con esta camiseta inspirada en metal. Descarada, auténtica, sin disculpas.',
                'estado': 'DISP',
                'precio': 27.00,
                'talla': 'M',
                'category': 'camisetas',
                'image_group': 'metal_shirt'
            },
            {
                'user': 'santiago',
                'nombre': 'Vaqueros Azul Marino Patrimonio',
                'descripcion': 'Vaquero azul marino con patrimonio. Construido para durar generaciones. Un básico de armario con alma.',
                'estado': 'DISP',
                'precio': 52.00,
                'talla': 'M',
                'category': 'pantalones',
                'image_group': 'n_jeans'
            },
            {
                'user': 'roberto',
                'nombre': 'Polo Marrón Elegante',
                'descripcion': 'Polo marrón elegante para cualquier ocasión. De casual a refinado, lo hace todo.',
                'estado': 'DISP',
                'precio': 40.00,
                'talla': 'L',
                'category': 'camisetas',
                'image_group': 'polo_brown'
            },
            {
                'user': 'andres',
                'nombre': 'Camisa Look Secundario',
                'descripcion': 'Camisa versátil perfecta para capas o usada sola. Tu nueva prenda favorita.',
                'estado': 'DISP',
                'precio': 36.00,
                'talla': 'L',
                'category': 'camisetas',
                'image_group': 'shirt2'
            },
        ]

        # Helper function to convert HEIC to JPEG if needed
        def convert_heic_to_jpeg_if_needed(image_path):
            if image_path.suffix.lower() == '.heic':
                try:
                    img = Image.open(image_path)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = rgb_img
                    output = BytesIO()
                    img.save(output, format='JPEG', quality=90)
                    output.seek(0)
                    return output, 'jpeg'
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Error converting {image_path.name}: {str(e)}'))
                    return None, None
            else:
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

            image_group_name = prod_info['image_group']
            if image_group_name in image_groups:
                order = 0
                sorted_images = sorted(
                    image_groups[image_group_name], 
                    key=lambda x: (0 if x['view_type'] == 'front' else 1, x['view_type'])
                )
                for img_info in sorted_images:
                    image_path = img_info['path']
                    image_data, image_format = convert_heic_to_jpeg_if_needed(image_path)
                    if image_data:
                        if isinstance(image_data, bytes):
                            filename = f"{image_group_name}_{order}.jpg"
                        else:
                            ext = 'jpg' if image_format == 'jpeg' else image_format
                            filename = f"{image_group_name}_{order}.{ext}"
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
            product_key += 1

        # Simple relations
        users['santiago'].friends.add(users['roberto'])
        users['santiago'].friends.add(users['andres'])
        users['roberto'].friends.add(users['beatriz'])
        users['andres'].friends.add(users['maria'])

        # Create friend requests
        fr1 = FriendRequest.objects.create(
            sender=users['beatriz'],
            recibidor2=users['roberto'],
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
            usuario2=users['roberto']
        )
        Mensaje.objects.create(
            conversation=conv1,
            sender=users['roberto'],
            contenido='¡Los vaqueros baggy son perfectos! ¿Siguen disponibles?'
        )
        Mensaje.objects.create(
            conversation=conv1,
            sender=users['santiago'],
            contenido='Sí, están disponibles. Gastados pero con mucha vida aún.'
        )
        Mensaje.objects.create(
            conversation=conv1,
            sender=users['roberto'],
            contenido='¡Me los llevo! ¿Puedes enviar a Barcelona?'
        )

        conv2 = Conversation.objects.create(
            producto=products[2],
            usuario1=users['andres'],
            usuario2=users['beatriz']
        )
        Mensaje.objects.create(
            conversation=conv2,
            sender=users['beatriz'],
            contenido='¡Amo la chaqueta de pana! Ese color es exactamente lo que buscaba.'
        )
        Mensaje.objects.create(
            conversation=conv2,
            sender=users['andres'],
            contenido='Es una prenda excelente. Muy cálida para el invierno.'
        )

        # Create sales and reviews
        from decimal import Decimal
        import uuid
        
        venta1 = Venta.objects.create(
            comprador=users['roberto'],
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
            comprador=users['beatriz'],
            vendedor=users['andres'],
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
            escritor=users['roberto'],
            recibidor=users['santiago'],
            venta=venta1,
            contenido='¡Vaqueros vintage hermosos! Exactamente como se describen. El vendedor es un verdadero profesional. ¡Cinco estrellas!',
            puntuacion=5
        )
        resena2 = Resena.objects.create(
            escritor=users['beatriz'],
            recibidor=users['andres'],
            venta=venta2,
            contenido='La chaqueta de pana es perfecta. Alta calidad, excelente ajuste. ¡Volvería a comprar!',
            puntuacion=5
        )

        # Create notifications
        Notification.objects.create(
            user=users['santiago'],
            tipo='venta',
            contenido='Roberto compró tus Vaqueros Baggy Vintage!',
            object_id=venta1.id
        )
        Notification.objects.create(
            user=users['andres'],
            tipo='venta',
            contenido='Beatriz compró tu Chaqueta de Pana!',
            object_id=venta2.id
        )

        self.stdout.write(self.style.SUCCESS('✓ Database populated (populate_db_3)'))
