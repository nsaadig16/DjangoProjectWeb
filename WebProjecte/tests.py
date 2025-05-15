import os
import time
import geckodriver_autoinstaller
from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from WebProjecte.models import Card, Rarity, CardSet, Profile, Collection, CollectionCard


### IMPORTANT ###
### Tests must be run in a virtual environment ###


class SeleniumTestBase(StaticLiveServerTestCase):
    """Base class for Selenium tests"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Automatically install geckodriver if not present
        geckodriver_autoinstaller.install()

        # Set up Firefox options for headless mode
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")

        # Initialize WebDriver with Firefox (geckodriver)
        cls.driver = webdriver.Firefox(
            service=Service(geckodriver_autoinstaller.install()),
            options=firefox_options
        )

        # Maximize the window
        cls.driver.maximize_window()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        # Create test data
        self.create_test_data()

    def create_test_data(self):
        """Create test data for the tests"""
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepassword123'
        )

        self.test_collection, created = Collection.objects.get_or_create(user=self.test_user)

        if created:
            print(f"Collection created for {self.test_user.username}")
        else:
            print(f"Collection already existed for {self.test_user.username}")

        self.test_rarity = Rarity.objects.create(
            title='Common',
            description='A common card',
            probability=0.7
        )

        self.test_card_set = CardSet.objects.create(
            title='Base Set',
            description='The base set of cards',
        )

        self.test_card = Card.objects.create(
            title='Test Card',
            description='This is a test card',
            rarity=self.test_rarity,
            card_set=self.test_card_set
        )

        CollectionCard.objects.create(
            card=self.test_card,
            collection=self.test_collection,
            quantity=1
        )

    def login(self, username='testuser', password='securepassword123'):
        """Helper method for logging in"""
        self.driver.get(f'{self.live_server_url}/login/')

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )

        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'password').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        WebDriverWait(self.driver, 10).until(
            EC.url_contains(self.live_server_url)
        )


class AuthenticationTest(SeleniumTestBase):
    """Authentication tests"""

    def test_user_creation_creates_only_one_collection(self):
        new_user = User.objects.create_user(
            username='onecoluser',
            email='onecol@example.com',
            password='password123'
        )
        if not Collection.objects.filter(user=new_user).exists():
            Collection.objects.create(user=new_user)
        self.assertEqual(Collection.objects.filter(user=new_user).count(), 1)

    def test_login_success(self):
        self.driver.get(f'{self.live_server_url}/login/')
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'username'))
            )
        except TimeoutException:
            self.fail("Login form did not load properly")

        self.assertIn('/login', self.driver.current_url)

        self.driver.find_element(By.NAME, 'username').send_keys('testuser')
        self.driver.find_element(By.NAME, 'password').send_keys('securepassword123')

        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_changes(f'{self.live_server_url}/login/')
            )
        except TimeoutException:
            self.fail("Login redirect failed")

        current_url = self.driver.current_url
        self.assertNotIn('/login', current_url)

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="/profile/"]'))
            )
        except TimeoutException:
            self.fail("Profile link not found after login")

    def test_login_failure(self):
        self.driver.get(f'{self.live_server_url}/login/')
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        self.driver.find_element(By.NAME, 'username').send_keys('testuser')
        self.driver.find_element(By.NAME, 'password').send_keys('wrongpassword')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.error p'))
            )
        except TimeoutException:
            self.fail("Error message not shown with invalid credentials")
        self.assertIn('/login', self.driver.current_url)

    def test_register(self):
        self.driver.get(f'{self.live_server_url}/register/')
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        username = 'newuser_register_test'
        email = 'new_register@example.com'
        password = 'securenewpassword123'
        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'email').send_keys(email)
        self.driver.find_element(By.NAME, 'password1').send_keys(password)
        self.driver.find_element(By.NAME, 'password2').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        WebDriverWait(self.driver, 10).until(
            EC.url_contains(self.live_server_url)
        )
        self.assertEqual(self.driver.current_url, f'{self.live_server_url}/')
        user = User.objects.get(username=username)
        collection_count = Collection.objects.filter(user=user).count()
        self.assertEqual(collection_count, 1)
        self.assertTrue(User.objects.filter(username=username).exists())

    def test_logout(self):
        self.login()
        self.assertNotIn('/login', self.driver.current_url)
        try:
            logout_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.btn.btn-danger[href="/logout/"]'))
            )
            logout_link.click()
        except TimeoutException:
            self.fail("Logout link not found")
        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_contains(self.live_server_url)
            )
        except TimeoutException:
            self.fail("Logout redirect failed")
        self.assertEqual(self.driver.current_url, f'{self.live_server_url}/')
        try:
            WebDriverWait(self.driver, 10).until_not(
                EC.presence_of_element_located((By.LINK_TEXT, 'testuser'))
            )
        except TimeoutException:
            self.fail("Username still visible after logout")
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.LINK_TEXT, 'Home'))
            )
        except TimeoutException:
            self.fail("Home link not found after logout")


class CardsTest(SeleniumTestBase):
    """Card functionality tests"""

    def test_view_cards_page(self):
        self.driver.get(f'{self.live_server_url}/card/')
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("Card page did not load properly")
        self.assertIn('card', self.driver.current_url)

    def test_api_cards(self):
        self.driver.get(f'{self.live_server_url}/api/cartas/')
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            page_source = self.driver.page_source
            self.assertTrue(
                'title' in page_source or
                'nombre' in page_source or
                'description' in page_source or
                'texto' in page_source,
                "JSON response does not contain expected fields"
            )
        except TimeoutException:
            self.fail("Card API did not return a response")

    def test_user_cards_api(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/api/mis-cartas/')
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            page_source = self.driver.page_source
            self.assertTrue(
                'title' in page_source or
                'nombre' in page_source or
                'quantity' in page_source or
                'cantidad' in page_source,
                "User card API JSON response does not contain expected fields"
            )
        except TimeoutException:
            self.fail("User card API did not return a response")


class ProfileTest(SeleniumTestBase):
    """User profile functionality tests"""

    def test_view_profile(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/profile/')
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("Profile page did not load properly")
        self.assertIn('profile', self.driver.current_url)
        self.assertIn('testuser', self.driver.page_source)

    def test_view_collection(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/coleccion/')
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("Collection page did not load properly")
        self.assertIn('coleccion', self.driver.current_url)

    def test_friends_list(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/friends/')
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("Friends page did not load properly")
        self.assertIn('friends', self.driver.current_url)


class GeneralPagesTest(SeleniumTestBase):
    """General pages tests"""

    def test_como_jugar_page(self):
        self.driver.get(f'{self.live_server_url}/como-jugar/')
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("How to play page did not load properly")
        self.assertIn('como-jugar', self.driver.current_url)

    def test_open_pack_page(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/select-pack/')
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("Select pack page did not load properly")
        self.assertIn('select-pack', self.driver.current_url)



