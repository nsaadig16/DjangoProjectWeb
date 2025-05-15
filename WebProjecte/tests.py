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
        """Ensure only one collection is created per user"""
        new_user = User.objects.create_user(
            username='onecoluser',
            email='onecol@example.com',
            password='password123'
        )

        if not Collection.objects.filter(user=new_user).exists():
            Collection.objects.create(user=new_user)

        self.assertEqual(Collection.objects.filter(user=new_user).count(), 1)

    def test_login_success(self):
        """Test successful login"""
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
            self.fail("Login redirect did not complete")

        current_url = self.driver.current_url
        self.assertNotIn('/login', current_url)

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="/profile/"]'))
            )
        except TimeoutException:
            self.fail("Login did not display profile link")

    def test_login_failure(self):
        """Test failed login"""

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
            self.fail("Error message not shown for wrong credentials")

        self.assertIn('/login', self.driver.current_url)

    def test_register(self):
        """Test user registration"""

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

        self.assertEqual(collection_count, 1, "Collection created more than once")

        self.assertTrue(
            User.objects.filter(username=username).exists(),
            "User was not created properly"
        )

    def test_logout(self):
        """Test logout"""

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
            self.fail("Logout redirect did not complete")

        self.assertEqual(self.driver.current_url, f'{self.live_server_url}/')
        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_to_be(f'{self.live_server_url}/')
            )
        except TimeoutException:
            self.fail("Did not land on home page after logout")

        try:
            WebDriverWait(self.driver, 10).until_not(
                EC.presence_of_element_located((By.LINK_TEXT, 'testuser'))
            )
        except TimeoutException:
            self.fail("User still visible after logout")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.LINK_TEXT, 'Home'))
            )
        except TimeoutException:
            self.fail("Logged-out state not confirmed")


class CardsTest(SeleniumTestBase):
    """Tests for card functionality"""

    def test_view_cards_page(self):
        """Test card page view"""

        self.driver.get(f'{self.live_server_url}/card/')

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("Card page did not load correctly")

        self.assertIn('card', self.driver.current_url)

    def test_api_cards(self):
        """Test card API"""

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
                "JSON response missing expected fields"
            )
        except TimeoutException:
            self.fail("Card API did not return a response")

    def test_user_cards_api(self):
        """Test user card API"""

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
                "JSON response missing expected fields"
            )
        except TimeoutException:
            self.fail("User card API did not return a response")


class ProfileTest(SeleniumTestBase):
    """Tests for user profile functionality"""

    def test_view_profile(self):
        """Test profile view"""

        self.login()

        self.driver.get(f'{self.live_server_url}/profile/')

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("Profile page did not load")

        self.assertIn('profile', self.driver.current_url)
        self.assertIn('testuser', self.driver.page_source)

    def test_view_collection(self):
        """Test collection view"""

        self.login()

        self.driver.get(f'{self.live_server_url}/coleccion/')

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("Collection page did not load")

        self.assertIn('coleccion', self.driver.current_url)

    def test_friends_list(self):
        """Test friend list view"""

        self.login()

        self.driver.get(f'{self.live_server_url}/friends/')

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("Friends page did not load")

        self.assertIn('friends', self.driver.current_url)


class GeneralPagesTest(SeleniumTestBase):
    """Tests for general pages"""

    def test_como_jugar_page(self):
        """Test 'how to play' page"""

        self.driver.get(f'{self.live_server_url}/como-jugar/')

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("How to play page did not load")
        self.assertIn('como-jugar', self.driver.current_url)

    def test_open_pack_page(self):
        """Test open pack page (only for logged-in users)"""

        self.login()

        self.driver.get(f'{self.live_server_url}/pack/open/')

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("Open pack page did not load")

        self.assertIn('pack/open', self.driver.current_url)
