from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Profile, Product, Category

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model creation and validation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation(self):
        """Test basic user creation"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_str(self):
        """Test user string representation"""
        self.assertEqual(str(self.user), 'testuser')


class ProfileModelTest(TestCase):
    """Test Profile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='pass123'
        )
        self.profile = Profile.objects.get(user=self.user)
    
    def test_profile_created_with_user(self):
        """Test that profile is created when user is created"""
        self.assertIsNotNone(self.profile)
        self.assertEqual(self.profile.user, self.user)
    
    def test_profile_default_values(self):
        """Test profile default values"""
        self.assertEqual(self.profile.num_amigos, 0)
        self.assertFalse(self.profile.is_banned)


class CategoryModelTest(TestCase):
    """Test Category model"""
    
    def setUp(self):
        self.category = Category.objects.create(name='Electronics')
    
    def test_category_creation(self):
        """Test category creation"""
        self.assertEqual(self.category.name, 'Electronics')
    
    def test_category_str(self):
        """Test category string representation"""
        self.assertEqual(str(self.category), 'Electronics')


class ProductModelTest(TestCase):
    """Test Product model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='pass123'
        )
        self.category = Category.objects.create(name='Clothing')
        self.product = Product.objects.create(
            nombre='Test Product',
            descripcion='A test product',
            precio=99.99,
            vendedor=self.user,
            categoria=self.category
        )
    
    def test_product_creation(self):
        """Test product creation"""
        self.assertEqual(self.product.nombre, 'Test Product')
        self.assertEqual(self.product.precio, 99.99)
        self.assertEqual(self.product.vendedor, self.user)
    
    def test_product_str(self):
        """Test product string representation"""
        self.assertEqual(str(self.product), 'Test Product')

