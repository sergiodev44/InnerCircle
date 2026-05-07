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
            password='testpass123',
            mobile=123456789
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
            password='pass123',
            mobile=987654321
        )
    
    def test_profile_exists(self):
        """Test that user model is working"""
        self.assertIsNotNone(self.user)
        self.assertEqual(self.user.username, 'profileuser')


class CategoryModelTest(TestCase):
    """Test Category model"""
    
    def setUp(self):
        self.category = Category.objects.create(
            nombre='Camisetas',
            descripcion='Camisetas de algodón'
        )
    
    def test_category_creation(self):
        """Test category creation"""
        self.assertEqual(self.category.nombre, 'Camisetas')
    
    def test_category_str(self):
        """Test category string representation"""
        self.assertEqual(str(self.category), 'Camisetas')


class ProductModelTest(TestCase):
    """Test Product model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='pass123',
            mobile=555555555
        )
        self.category = Category.objects.create(
            nombre='Camisetas',
            descripcion='Camisetas'
        )
    
    def test_user_creation_for_product(self):
        """Test that seller user is created properly"""
        self.assertEqual(self.user.username, 'seller')
        self.assertTrue(self.user.mobile)
    
    def test_category_creation_for_product(self):
        """Test that category is created properly"""
        self.assertEqual(self.category.nombre, 'Camisetas')


