import time
import geckodriver_autoinstaller
from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from WebProjecte.models import Card, Rarity, CardSet, Profile, Collection, CollectionCard


class SeleniumTestBase(StaticLiveServerTestCase):
    """Base Selenium test class with setup and teardown"""

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
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepassword123'
        )
        self.test_collection, _ = Collection.objects.get_or_create(user=self.test_user)

        # Dummy image to avoid failure in required ImageField
        dummy_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x02\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x02\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B',
            content_type='image/jpeg'
        )

        self.rarity = Rarity.objects.create(title='Common', description='Common', probability=0.7)
        self.card_set = CardSet.objects.create(
            title='Base Set',
            description='Base set',
            image=dummy_image
        )
        self.card = Card.objects.create(
            title='Test Card',
            description='This is a test card',
            rarity=self.rarity,
            card_set=self.card_set,
            image=dummy_image
        )
        CollectionCard.objects.create(card=self.card, collection=self.test_collection, quantity=1)

    def login(self, username='testuser', password='securepassword123'):
        self.driver.get(f'{self.live_server_url}/login/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'password').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        WebDriverWait(self.driver, 10).until_not(EC.url_contains('/login'))


class AuthenticationTest(SeleniumTestBase):
    """Test login, logout and registration"""

    def test_login_success(self):
        self.login()
        self.assertNotIn('/login', self.driver.current_url)

    def test_login_failure(self):
        self.driver.get(f'{self.live_server_url}/login/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
        self.driver.find_element(By.NAME, 'username').send_keys('testuser')
        self.driver.find_element(By.NAME, 'password').send_keys('wrongpassword')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        self.assertIn('/login', self.driver.current_url)

    def test_register(self):
        self.driver.get(f'{self.live_server_url}/register/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))

        self.driver.find_element(By.NAME, 'username').send_keys('newuser')
        self.driver.find_element(By.NAME, 'email').send_keys('new@example.com')
        self.driver.find_element(By.NAME, 'password1').send_keys('newpass123')
        self.driver.find_element(By.NAME, 'password2').send_keys('newpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        WebDriverWait(self.driver, 10).until_not(EC.url_contains('/register'))
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertEqual(Collection.objects.filter(user__username='newuser').count(), 1)

    def test_logout(self):
        self.login()
        dropdown_toggle = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'navbarDropdown'))
        )
        dropdown_toggle.click()

        logout_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.dropdown-item.text-danger[href="/logout/"]'))
        )
        logout_btn.click()

    def test_single_collection_per_user(self):
        user = User.objects.create_user('uniqueuser', 'unique@example.com', 'unique123')
        Collection.objects.get_or_create(user=user)
        self.assertEqual(Collection.objects.filter(user=user).count(), 1)


class CardsTest(SeleniumTestBase):
    """Card views and API"""

    def test_api_cards(self):
        self.driver.get(f'{self.live_server_url}/api/cards/')
        body = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        self.assertIn('Test Card', body.text)

    def test_user_cards_api_authenticated(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/api/my-cards/')
        body = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        self.assertTrue('Test Card' in body.text or 'quantity' in body.text)


class ProfileTest(SeleniumTestBase):
    """Profile and collection pages"""

    def test_view_profile(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/profile/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        self.assertIn('testuser', self.driver.page_source)

    def test_view_collection(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/collection/')
        self.assertIn('collection', self.driver.current_url)

    def test_view_friends(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/friends/')
        self.assertIn('friends', self.driver.current_url)


class GeneralPagesTest(SeleniumTestBase):
    """Generic public and restricted pages"""

    def test_home_page(self):
        self.driver.get(f'{self.live_server_url}/')
        self.assertIn('home', self.driver.title.lower())

    def test_how_to_play_page(self):
        self.driver.get(f'{self.live_server_url}/how-to-play/')
        self.assertIn('how-to-play', self.driver.current_url)

    def test_select_pack(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/select-pack/')
        self.assertIn('select-pack', self.driver.current_url)
