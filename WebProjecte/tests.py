import os
import tempfile
import time
import geckodriver_autoinstaller
from PIL import Image
from django.test import TestCase, Client
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth import authenticate
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, ElementClickInterceptedException
from WebProjecte.models import Card, Rarity, CardSet, Profile, Collection, CollectionCard, UserCard


class HybridTestBase(StaticLiveServerTestCase):
    """Base class that combines Django Test Client with Selenium for E2E testing"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        geckodriver_autoinstaller.install()
        options = Options()
        options.add_argument("--headless")
        cls.driver = webdriver.Firefox(
            service=Service(geckodriver_autoinstaller.install()),
            options=options
        )
        cls.driver.maximize_window()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        # Django Test Client for backend operations
        self.client = Client()

        # Create test data using Django ORM (faster than UI)
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepassword123'
        )
        self.test_collection, _ = Collection.objects.get_or_create(user=self.test_user)

        # Create test data
        self.dummy_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x02\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x02\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B',
            content_type='image/jpeg'
        )

        self.rarity = Rarity.objects.create(title='Common', description='Common', probability=0.7)
        self.card_set = CardSet.objects.create(
            title='Base Set',
            description='Base set',
            image=self.dummy_image
        )
        self.card = Card.objects.create(
            title='Test Card',
            description='This is a test card',
            rarity=self.rarity,
            card_set=self.card_set,
            image=self.dummy_image
        )
        CollectionCard.objects.create(card=self.card, collection=self.test_collection, quantity=1)

    def login_via_client(self, username='testuser', password='securepassword123'):
        """Login using Django Test Client (faster for setup)"""
        return self.client.login(username=username, password=password)

    def login_via_selenium(self, username='testuser', password='securepassword123'):
        """Login using Selenium (for UI testing)"""
        self.driver.get(f'{self.live_server_url}/login/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'password').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        WebDriverWait(self.driver, 10).until_not(EC.url_contains('/login'))

    def create_test_user_via_client(self, username, email, password):
        """Create user using Django ORM (faster than UI registration)"""
        user = User.objects.create_user(username=username, email=email, password=password)
        Collection.objects.get_or_create(user=user)
        return user

    def delete_user_via_selenium(self, username, password):
        """Delete user through UI - only when testing the delete functionality"""
        try:
            self.login_via_selenium(username, password)
            self.driver.get(f'{self.live_server_url}/profile/')

            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            time.sleep(2)

            delete_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'delete-account-btn'))
            )

            # Robust clicking strategy
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                delete_btn
            )
            time.sleep(1)

            try:
                delete_btn.click()
            except (ElementClickInterceptedException, WebDriverException):
                self.driver.execute_script("arguments[0].click();", delete_btn)

            # Handle modal
            modal = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, 'deleteAccountModal'))
            )

            confirm_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'confirm-username'))
            )
            confirm_input.clear()
            confirm_input.send_keys(username)

            confirm_delete_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'confirm-delete-btn'))
            )

            try:
                confirm_delete_btn.click()
            except (ElementClickInterceptedException, WebDriverException):
                self.driver.execute_script("arguments[0].click();", confirm_delete_btn)

            WebDriverWait(self.driver, 10).until(
                EC.url_contains(f'{self.live_server_url}/')
            )
            return True

        except Exception as e:
            print(f"Error deleting user {username}: {e}")
            return False


class AuthenticationHybridTest(HybridTestBase):
    """Hybrid authentication tests - use client for setup, selenium for UI testing"""

    def test_login_success_ui(self):
        """Test successful login through UI"""
        self.login_via_selenium()
        self.assertNotIn('/login', self.driver.current_url)

    def test_login_failure_ui(self):
        """Test failed login through UI"""
        self.driver.get(f'{self.live_server_url}/login/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
        self.driver.find_element(By.NAME, 'username').send_keys('testuser')
        self.driver.find_element(By.NAME, 'password').send_keys('wrongpassword')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        self.assertIn('/login', self.driver.current_url)

    def test_register_backend_validation(self):
        """Test registration backend logic using Django client"""
        response = self.client.post('/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })

        # Check backend logic
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertEqual(Collection.objects.filter(user__username='newuser').count(), 1)

        # Clean up
        User.objects.get(username='newuser').delete()

    def test_register_ui_flow(self):
        """Test registration UI flow with selenium"""
        self.driver.get(f'{self.live_server_url}/register/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))

        username = 'newuser_ui'
        password = 'newpass123'

        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'email').send_keys('new@example.com')
        self.driver.find_element(By.NAME, 'password1').send_keys(password)
        self.driver.find_element(By.NAME, 'password2').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        WebDriverWait(self.driver, 10).until_not(EC.url_contains('/register'))

        # Verify with backend
        self.assertTrue(User.objects.filter(username=username).exists())

        # Clean up via UI (testing delete functionality)
        self.delete_user_via_selenium(username, password)
        self.assertFalse(User.objects.filter(username=username).exists())

    def test_logout_ui(self):
        """Test logout through UI"""
        self.login_via_selenium()
        dropdown_toggle = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'navbarDropdown'))
        )
        dropdown_toggle.click()

        logout_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.dropdown-item.text-danger[href="/logout/"]'))
        )
        logout_btn.click()


class CardsHybridTest(HybridTestBase):
    """Hybrid card tests - backend for data validation, UI for user interactions"""

    def test_cards_api_backend(self):
        """Test cards API using Django client"""
        response = self.client.get('/api/cards/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Card', response.content.decode())

    def test_cards_api_ui(self):
        """Test cards API through browser"""
        self.driver.get(f'{self.live_server_url}/api/cards/')
        body = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        self.assertIn('Test Card', body.text)

    def test_user_cards_api_backend(self):
        """Test authenticated user cards API using Django client"""
        self.login_via_client()
        response = self.client.get('/api/my-cards/')
        self.assertEqual(response.status_code, 200)
        response_text = response.content.decode()
        self.assertTrue('Test Card' in response_text or 'quantity' in response_text)

    def test_user_cards_api_ui(self):
        """Test authenticated user cards API through browser"""
        self.login_via_selenium()
        self.driver.get(f'{self.live_server_url}/api/my-cards/')
        body = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        self.assertTrue('Test Card' in body.text or 'quantity' in body.text)


class ProfileHybridTest(HybridTestBase):
    """Hybrid profile tests - backend for data, UI for interactions"""

    def test_profile_access_backend(self):
        """Test profile access using Django client"""
        self.login_via_client()
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')

    def test_profile_ui(self):
        """Test profile page through browser"""
        self.login_via_selenium()
        self.driver.get(f'{self.live_server_url}/profile/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        self.assertIn('testuser', self.driver.page_source)

    def test_collection_access_backend(self):
        """Test collection access using Django client"""
        self.login_via_client()
        response = self.client.get('/collection/')
        self.assertEqual(response.status_code, 200)

    def test_collection_ui(self):
        """Test collection page through browser"""
        self.login_via_selenium()
        self.driver.get(f'{self.live_server_url}/collection/')
        self.assertIn('collection', self.driver.current_url)


    def test_delete_account_ui_flow(self):
        """Test delete account UI interaction"""
        username = 'deleteuser_ui'
        password = 'deletepass123'

        # Create user using backend (faster)
        user = self.create_test_user_via_client(username, 'delete@example.com', password)

        # Test UI flow
        success = self.delete_user_via_selenium(username, password)
        self.assertTrue(success, "Failed to delete user via UI")
        self.assertFalse(User.objects.filter(username=username).exists())

    def test_delete_account_wrong_username_ui(self):
        """Test delete account with wrong username through UI"""
        username = 'wronguser_ui'
        password = 'wrongpass123'

        user = self.create_test_user_via_client(username, 'wrong@example.com', password)

        try:
            self.login_via_selenium(username, password)
            self.driver.get(f'{self.live_server_url}/profile/')

            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            time.sleep(2)

            delete_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'delete-account-btn'))
            )

            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                delete_btn
            )
            time.sleep(1)

            try:
                delete_btn.click()
            except (ElementClickInterceptedException, WebDriverException):
                self.driver.execute_script("arguments[0].click();", delete_btn)

            modal = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, 'deleteAccountModal'))
            )

            confirm_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'confirm-username'))
            )
            confirm_input.clear()
            confirm_input.send_keys('wrongusername')  # Wrong username

            time.sleep(2)  # Wait for validation

            confirm_delete_btn = self.driver.find_element(By.ID, 'confirm-delete-btn')
            is_disabled = not confirm_delete_btn.is_enabled() or confirm_delete_btn.get_attribute('disabled')

            self.assertTrue(is_disabled, "Delete button should be disabled with wrong username")
            self.assertTrue(User.objects.filter(username=username).exists(), "User should still exist")

        finally:
            # Clean up
            if User.objects.filter(username=username).exists():
                User.objects.get(username=username).delete()


class GeneralPagesHybridTest(HybridTestBase):
    """Test general pages - mix of backend and UI testing"""

    def test_public_pages_backend(self):
        """Test public pages access using Django client"""
        pages = ['/', '/how-to-play/']
        for page in pages:
            response = self.client.get(page)
            self.assertEqual(response.status_code, 200)

    def test_home_page_ui(self):
        """Test home page through browser"""
        self.driver.get(f'{self.live_server_url}/')
        self.assertIn('home', self.driver.title.lower())

    def test_how_to_play_ui(self):
        """Test how to play page through browser"""
        self.driver.get(f'{self.live_server_url}/how-to-play/')
        self.assertIn('how-to-play', self.driver.current_url)

    def test_authenticated_pages_backend(self):
        """Test authenticated pages using Django client"""
        self.login_via_client()
        response = self.client.get('/select-pack/')
        self.assertEqual(response.status_code, 200)

    def test_select_pack_ui(self):
        """Test select pack page through browser"""
        self.login_via_selenium()
        self.driver.get(f'{self.live_server_url}/select-pack/')
        self.assertIn('select-pack', self.driver.current_url)


class CardUploadHybridTest(HybridTestBase):
    """Hybrid card upload tests - backend validation + UI interaction"""

    def create_test_image(self):
        """Create test image file"""
        image = Image.new('RGB', (100, 100), color='blue')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(temp_file.name)
        return temp_file.name

    def test_card_upload_backend_validation(self):
        """Test card upload validation using Django client"""
        self.login_via_client()

        # Test validation errors
        response = self.client.post('/add-card/', {})
        self.assertEqual(response.status_code, 200)  # Form validation fails, stays on page

        # Test successful upload
        with open(self.create_test_image(), 'rb') as img:
            response = self.client.post('/add-card/', {
                'title': 'Backend Card',
                'description': 'Backend uploaded card',
                'image': img,
                'rarity': self.rarity.id
            })

        # Should redirect after successful upload
        self.assertEqual(response.status_code, 302)
        self.assertTrue(UserCard.objects.filter(title='Backend Card').exists())

    def test_card_upload_ui_flow(self):
        """Test card upload through UI"""
        self.login_via_selenium()
        image_path = self.create_test_image()

        self.driver.get(f'{self.live_server_url}/add-card/')

        self.driver.find_element(By.NAME, 'title').send_keys('UI Card')
        self.driver.find_element(By.NAME, 'description').send_keys('UI uploaded card')
        self.driver.find_element(By.NAME, 'image').send_keys(image_path)
        # Assuming rarity dropdown exists
        self.driver.find_element(By.NAME, 'rarity').send_keys('Common')
        self.driver.find_element(By.TAG_NAME, 'form').submit()

        WebDriverWait(self.driver, 10).until_not(EC.url_contains('/add-card/'))

        # Verify in backend
        self.assertTrue(UserCard.objects.filter(title='UI Card').exists())

        # Clean up
        os.unlink(image_path)

    def test_card_replacement_logic(self):
        """Test that previous cards are replaced - backend logic"""
        self.login_via_client()

        # Create first card
        with open(self.create_test_image(), 'rb') as img:
            self.client.post('/add-card/', {
                'title': 'Card 1',
                'description': 'First card',
                'image': img,
                'rarity': self.rarity.id
            })

        # Create second card
        with open(self.create_test_image(), 'rb') as img:
            self.client.post('/add-card/', {
                'title': 'Card 2',
                'description': 'Second card',
                'image': img,
                'rarity': self.rarity.id
            })

        # Verify replacement logic
        cards = UserCard.objects.filter(user=self.test_user)
        self.assertEqual(cards.count(), 1)
        self.assertEqual(cards.first().title, 'Card 2')


class CleanupHybridTest(HybridTestBase):
    """Cleanup test using backend for efficiency"""

    def test_cleanup_all_test_users(self):
        """Clean up test users using Django ORM (much faster)"""
        test_usernames = ['testuser', 'newuser', 'newuser_ui', 'uniqueuser', 'deleteuser',
                          'deleteuser_ui', 'wronguser_ui', 'wrongdeleteuser']

        for username in test_usernames:
            try:
                if User.objects.filter(username=username).exists():
                    User.objects.get(username=username).delete()
                    print(f"Deleted user: {username}")
            except Exception as e:
                print(f"Error deleting user {username}: {e}")

    def tearDown(self):
        """Clean up after each test using Django ORM"""
        super().tearDown()
        # Clean up any test users that might have been created
        test_users = User.objects.filter(username__startswith='test')
        for user in test_users:
            try:
                user.delete()
            except:
                pass