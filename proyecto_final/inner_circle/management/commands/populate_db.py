from django.core.management.base import BaseCommand
from inner_circle.models import User, Profile, Product, FriendRequest
from django.core.files.base import ContentFile
from PIL import Image
import io


class Command(BaseCommand):
    help = 'Populate database with test data'

    def handle(self, *args, **options):
        # Create users
        user1 = User.objects.create_user(
            username='john', 
            password='spaceone0',
            email='john@test.com',
            mobile=123456789
        )
        user2 = User.objects.create_user(
            username='drake', 
            password='spaceone0',
            email='drake@test.com',
            mobile=987654321
        )
        user3 = User.objects.create_user(
            username='myles', 
            password='spaceone0',
            email='myles@test.com',
            mobile=555666777
        )

        # Create profiles
        profile1 = Profile.objects.create(
            user=user1,
            nombre_tag='John Doe',
            bio='Love trading clothes'
        )
        profile2 = Profile.objects.create(
            user=user2,
            nombre_tag='Drake Fan',
            bio='Selling vintage gear'
        )
        profile3 = Profile.objects.create(
            user=user3,
            nombre_tag='Myles Cool',
            bio='Minimalist style'
        )

        # Create products
        product1 = Product.objects.create(
            user=user1,
            nombre='Blue Jacket',
            descripcion='Vintage blue denim jacket',
            estado='DISP',
            precio=29.99,
            talla='M'
        )
        product2 = Product.objects.create(
            user=user2,
            nombre='Red Shirt',
            descripcion='Cotton red shirt, barely worn',
            estado='DISP',
            precio=15.99,
            talla='L'
        )
        product3 = Product.objects.create(
            user=user3,
            nombre='Black Pants',
            descripcion='Slim fit black trousers',
            estado='DISP',
            precio=45.00,
            talla='M'
        )

        # Create friendships
        user1.friends.add(user2)
        user1.friends.add(user3)
        user2.friends.add(user3)

        # Create friend requests
        FriendRequest.objects.create(
            sender=user2,
            recibidor2=user3,
            status='pendiente'
        )

        self.stdout.write(
            self.style.SUCCESS('Database populated successfully!')
        )
        self.stdout.write(f'Created users: john, drake, myles')
        self.stdout.write(f'Created friendships')
        self.stdout.write(f'Created 3 products')
