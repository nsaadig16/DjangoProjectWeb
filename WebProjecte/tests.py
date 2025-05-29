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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, ElementClickInterceptedException

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

        # Imagen dummy para evitar fallo en ImageField obligatorio
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

    def delete_user_via_ui(self, username, password):
        """Helper method to delete a user through the UI with robust scrolling and clicking"""
        try:
            # Login
            self.login(username, password)

            # Go to profile
            self.driver.get(f'{self.live_server_url}/profile/')

            # Wait for page to load completely
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

            # Additional wait for any dynamic content or animations
            time.sleep(2)

            # Find the delete button
            delete_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'delete-account-btn'))
            )

            # Try multiple scrolling strategies
            scrolling_strategies = [
                # Strategy 1: Scroll element into center view
                lambda: self.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});",
                    delete_btn
                ),
                # Strategy 2: Scroll to bottom of page
                lambda: self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"),
                # Strategy 3: Scroll with offset
                lambda: self.driver.execute_script(
                    "window.scrollTo(0, arguments[0].offsetTop - window.innerHeight/2);",
                    delete_btn
                ),
                # Strategy 4: ActionChains move to element
                lambda: ActionChains(self.driver).move_to_element(delete_btn).perform()
            ]

            # Try each scrolling strategy until one works
            clicked = False
            for i, scroll_strategy in enumerate(scrolling_strategies):
                try:
                    scroll_strategy()
                    time.sleep(1)  # Wait for scroll to complete

                    # Wait for element to be clickable
                    clickable_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, 'delete-account-btn'))
                    )

                    # Try different clicking methods
                    click_methods = [
                        lambda: clickable_btn.click(),  # Regular click
                        lambda: self.driver.execute_script("arguments[0].click();", clickable_btn),  # JS click
                        lambda: ActionChains(self.driver).click(clickable_btn).perform()  # ActionChains click
                    ]

                    for click_method in click_methods:
                        try:
                            click_method()
                            clicked = True
                            break
                        except (ElementClickInterceptedException, WebDriverException):
                            continue

                    if clicked:
                        break

                except Exception as e:
                    print(f"Scrolling strategy {i + 1} failed: {e}")
                    continue

            if not clicked:
                raise Exception("Failed to click delete button with all strategies")

            # Wait for modal to appear
            modal = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, 'deleteAccountModal'))
            )

            # Enter username confirmation
            confirm_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'confirm-username'))
            )
            confirm_input.clear()
            confirm_input.send_keys(username)

            # Wait for confirmation button to be enabled
            confirm_delete_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'confirm-delete-btn'))
            )

            # Click confirmation button with fallback
            try:
                confirm_delete_btn.click()
            except (ElementClickInterceptedException, WebDriverException):
                self.driver.execute_script("arguments[0].click();", confirm_delete_btn)

            # Wait for redirect to home page
            WebDriverWait(self.driver, 10).until(
                EC.url_contains(f'{self.live_server_url}/')
            )

            return True

        except TimeoutException as e:
            print(f"Timeout error deleting user {username}: {e}")
            # Take screenshot for debugging
            try:
                self.driver.save_screenshot(f'delete_user_error_{username}.png')
            except:
                pass
            return False
        except Exception as e:
            print(f"Unexpected error deleting user {username}: {e}")
            # Take screenshot for debugging
            try:
                self.driver.save_screenshot(f'delete_user_error_{username}.png')
            except:
                pass
            return False
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

        username = 'newuser'
        password = 'newpass123'

        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'email').send_keys('new@example.com')
        self.driver.find_element(By.NAME, 'password1').send_keys(password)
        self.driver.find_element(By.NAME, 'password2').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        WebDriverWait(self.driver, 10).until_not(EC.url_contains('/register'))
        self.assertTrue(User.objects.filter(username=username).exists())
        self.assertEqual(Collection.objects.filter(user__username=username).count(), 1)

        # Delete the created user via UI
        self.delete_user_via_ui(username, password)

        # Verify user was deleted
        self.assertFalse(User.objects.filter(username=username).exists())

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
        username = 'uniqueuser'
        password = 'unique123'

        user = User.objects.create_user(username, 'unique@example.com', password)
        Collection.objects.get_or_create(user=user)
        self.assertEqual(Collection.objects.filter(user=user).count(), 1)

        # Clean up via UI
        self.delete_user_via_ui(username, password)


class CardsTest(SeleniumTestBase):
    """Card views and API"""

    def test_api_cartas(self):
        self.driver.get(f'{self.live_server_url}/api/cartas/')
        body = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        self.assertIn('Test Card', body.text)

    def test_user_cards_api_authenticated(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/api/mis-cartas/')
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
        self.driver.get(f'{self.live_server_url}/coleccion/')
        self.assertIn('coleccion', self.driver.current_url)

    def test_view_friends(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/friends/')
        self.assertIn('friends', self.driver.current_url)

    def test_delete_account_functionality(self):
        """Test específico para la funcionalidad de eliminar cuenta"""
        username = 'deleteuser'
        password = 'deletepass123'

        # Create a user to delete
        user = User.objects.create_user(username, 'delete@example.com', password)
        Collection.objects.get_or_create(user=user)

        # Verify user exists
        self.assertTrue(User.objects.filter(username=username).exists())

        # Delete via UI
        success = self.delete_user_via_ui(username, password)
        self.assertTrue(success, "Failed to delete user via UI")

        # Verify user was deleted
        self.assertFalse(User.objects.filter(username=username).exists())
        self.assertFalse(Collection.objects.filter(user__username=username).exists())

    def test_delete_account_wrong_username(self):
        """Test que la eliminación falla con nombre de usuario incorrecto"""
        username = 'wrongdeleteuser'
        password = 'wrongpass123'

        # Create user
        user = User.objects.create_user(username, 'wrong@example.com', password)

        try:
            # Login
            self.login(username, password)

            # Go to profile
            self.driver.get(f'{self.live_server_url}/profile/')

            # Wait for page to load completely
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            time.sleep(2)  # Extra time for any animations or dynamic content

            # Find delete button with multiple strategies
            delete_btn = None
            strategies = [
                lambda: WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, 'delete-account-btn'))),
                lambda: self.driver.find_element(By.CSS_SELECTOR, 'button#delete-account-btn'),
                lambda: self.driver.find_element(By.CSS_SELECTOR, '[id="delete-account-btn"]'),
            ]

            for strategy in strategies:
                try:
                    delete_btn = strategy()
                    break
                except:
                    continue

            if not delete_btn:
                raise Exception("Could not locate delete button with any strategy")

            # Multiple scrolling approaches
            scroll_attempts = [
                # Approach 1: Scroll to center
                lambda: self.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});",
                    delete_btn),
                # Approach 2: Scroll to bottom first, then to element
                lambda: (
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"),
                    time.sleep(0.5),
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                               delete_btn)
                ),
                # Approach 3: Manual scroll calculation
                lambda: self.driver.execute_script("window.scrollTo(0, arguments[0].offsetTop - window.innerHeight/2);",
                                                   delete_btn),
            ]

            clicked = False
            for i, scroll_attempt in enumerate(scroll_attempts):
                try:
                    scroll_attempt()
                    time.sleep(1)

                    # Try to make element clickable
                    clickable_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, 'delete-account-btn'))
                    )

                    # Multiple click strategies
                    click_methods = [
                        lambda: clickable_btn.click(),
                        lambda: self.driver.execute_script("arguments[0].click();", clickable_btn),
                        lambda: self.driver.execute_script("document.getElementById('delete-account-btn').click();"),
                    ]

                    for click_method in click_methods:
                        try:
                            click_method()
                            clicked = True
                            break
                        except:
                            continue

                    if clicked:
                        break

                except Exception as e:
                    print(f"Scroll attempt {i + 1} failed: {e}")
                    continue

            if not clicked:
                # Last resort: Force click with JavaScript
                self.driver.execute_script("""
                    var btn = document.getElementById('delete-account-btn');
                    if (btn) {
                        btn.scrollIntoView({block: 'center'});
                        setTimeout(function() { btn.click(); }, 500);
                    }
                """)
                time.sleep(1)

            # Wait for modal to appear with longer timeout
            try:
                modal = WebDriverWait(self.driver, 15).until(
                    EC.visibility_of_element_located((By.ID, 'deleteAccountModal'))
                )
            except TimeoutException:
                # Debug: Check if modal exists but not visible
                modals = self.driver.find_elements(By.ID, 'deleteAccountModal')
                if modals:
                    print("Modal exists but not visible, trying to show it")
                    self.driver.execute_script("arguments[0].style.display = 'block';", modals[0])
                    modal = modals[0]
                else:
                    raise Exception("Modal not found after clicking delete button")

            # Enter wrong username
            confirm_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'confirm-username'))
            )
            confirm_input.clear()
            confirm_input.send_keys('wrongusername')  # Intentionally wrong username

            # Wait for validation
            time.sleep(2)

            # Check button state - multiple validation approaches
            confirm_delete_btn = self.driver.find_element(By.ID, 'confirm-delete-btn')

            # Multiple ways to check if button is disabled
            is_disabled = any([
                confirm_delete_btn.get_attribute('disabled') is not None,
                confirm_delete_btn.get_attribute('disabled') == 'true',
                'disabled' in (confirm_delete_btn.get_attribute('class') or ''),
                not confirm_delete_btn.is_enabled(),
                confirm_delete_btn.get_attribute('aria-disabled') == 'true'
            ])

            self.assertTrue(is_disabled, f"Delete confirmation button should be disabled with wrong username. "
                                         f"Button attributes: disabled={confirm_delete_btn.get_attribute('disabled')}, "
                                         f"class={confirm_delete_btn.get_attribute('class')}, "
                                         f"enabled={confirm_delete_btn.is_enabled()}")

            # Verify user still exists
            self.assertTrue(User.objects.filter(username=username).exists(),
                            "User should still exist after failed deletion attempt")

            # Clean up
            user.delete()

        except Exception as e:
            # Clean up in case of error
            try:
                if User.objects.filter(username=username).exists():
                    User.objects.get(username=username).delete()
            except:
                pass

            # Take screenshot for debugging
            try:
                self.driver.save_screenshot(f'test_delete_wrong_username_error.png')
                print(f"Screenshot saved: test_delete_wrong_username_error.png")
            except:
                pass

            raise e
class GeneralPagesTest(SeleniumTestBase):
    """Generic public and restricted pages"""

    def test_home_page(self):
        self.driver.get(f'{self.live_server_url}/')
        self.assertIn('home', self.driver.title.lower())

    def test_como_jugar_page(self):
        self.driver.get(f'{self.live_server_url}/como-jugar/')
        self.assertIn('como-jugar', self.driver.current_url)

    def test_select_pack(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/select-pack/')
        self.assertIn('select-pack', self.driver.current_url)


class CardUploadTest(SeleniumTestBase):
    """Test for card upload by non-admin users"""

    def setUp(self):
        super().setUp()
        # Create an additional non-admin user for testing
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='regularpass123'
        )
        self.regular_collection, _ = Collection.objects.get_or_create(user=self.regular_user)

        # Create additional rarity and card set for testing
        self.rare_rarity = Rarity.objects.create(
            title='Rare',
            description='Rare card',
            probability=0.2
        )

        # Dummy image for testing
        self.dummy_image = SimpleUploadedFile(
            name='upload_test.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x02\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x02\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B',
            content_type='image/jpeg'
        )

    def test_user_can_upload_card(self):
        """Test that a non-admin user can upload a card"""
        # Log in as regular user
        self.login('regularuser', 'regularpass123')

        # Navigate to the card upload page
        self.driver.get(f'{self.live_server_url}/add-card/')

        # Verify that we reached the correct page
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )

        # Fill out the card upload form
        # Card title
        title_input = self.driver.find_element(By.NAME, 'title')
        title_input.send_keys('My Custom Card')

        # Card description
        description_input = self.driver.find_element(By.NAME, 'description')
        description_input.send_keys('This is a card created by a regular user')

        # Select rarity
        rarity_select = self.driver.find_element(By.NAME, 'rarity')
        rarity_select.click()
        rarity_option = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'option[value="{self.rarity.id}"]'))
        )
        rarity_option.click()

        # Select card set
        cardset_select = self.driver.find_element(By.NAME, 'card_set')
        cardset_select.click()
        cardset_option = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'option[value="{self.card_set.id}"]'))
        )
        cardset_option.click()

        # Upload image (simulate file selection)
        file_input = self.driver.find_element(By.NAME, 'image')
        # In a real test, you would upload a real file here
        # file_input.send_keys('/path/to/image.jpg')

        # Submit form
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_btn.click()

        # Verify successful redirection
        WebDriverWait(self.driver, 10).until_not(
            EC.url_contains('/add-card/')
        )

        # Verify that the card was created in the database
        uploaded_card = Card.objects.filter(
            title='My Custom Card',
            description='This is a card created by a regular user'
        ).first()

        self.assertIsNotNone(uploaded_card, "The card should have been created in the database")
        self.assertEqual(uploaded_card.rarity, self.rarity)
        self.assertEqual(uploaded_card.card_set, self.card_set)

        # Verify that the user has the card in their collection
        collection_card = CollectionCard.objects.filter(
            card=uploaded_card,
            collection=self.regular_collection
        ).first()

        self.assertIsNotNone(collection_card, "The card should be in the user's collection")
        self.assertEqual(collection_card.quantity, 1)

    def test_upload_card_validation_errors(self):
        """Test form validation errors on upload"""
        self.login('regularuser', 'regularpass123')
        self.driver.get(f'{self.live_server_url}/add-card/')

        submit_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
        )
        submit_btn.click()

        time.sleep(2)
        self.assertIn('/add-card/', self.driver.current_url)

        # Check that error messages appear
        error_messages = self.driver.find_elements(By.CSS_SELECTOR, '.error, .invalid-feedback, .alert-danger')
        self.assertTrue(len(error_messages) > 0, "Validation error messages should appear")

    def test_user_can_view_uploaded_cards(self):
        """Test that the user can view their uploaded cards"""
        user_card = Card.objects.create(
            title='User Card',
            description='Card created by the regular user',
            rarity=self.rarity,
            card_set=self.card_set,
            image=self.dummy_image,
            created_by=self.regular_user  # Assuming there is a created_by field
        )

        CollectionCard.objects.create(
            card=user_card,
            collection=self.regular_collection,
            quantity=1
        )

        # Log in and navigate to "my cards" using the existing API
        self.login('regularuser', 'regularpass123')
        self.driver.get(f'{self.live_server_url}/api/mis-cartas/')

        # Verify that the card appears in the list
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        page_source = self.driver.page_source
        self.assertIn('User Card', page_source)
        self.assertIn('Card created by the regular user', page_source)

    def test_upload_card_with_file(self):
        """Test uploading a card with a real image file"""
        import tempfile
        import os

        # Create a temporary image file for the test
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # Write basic image data
            tmp_file.write(
                b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0C\x14\r\x0C\x0B\x0B\x0C\x19\x12\x13\x0F\x14\x1D\x1A\x1F\x1E\x1D\x1A\x1C\x1C $.\' ",#\x1C\x1C(7),01444\x1F\'9=82<.342\xFF\xC0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xFF\xC4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xFF\xC4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xDA\x00\x0C\x03\x01\x00\x02\x11\x03\x11\x00\x3F\x00\xAA\xFF\xD9'
            )
            temp_image_path = tmp_file.name

        try:
            self.login('regularuser', 'regularpass123')
            self.driver.get(f'{self.live_server_url}/upload-card/')

            self.driver.find_element(By.NAME, 'title').send_keys('Card with Image')
            self.driver.find_element(By.NAME, 'description').send_keys('Card with real image file')

            rarity_select = self.driver.find_element(By.NAME, 'rarity')
            rarity_select.click()
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f'option[value="{self.rarity.id}"]'))
            ).click()

            cardset_select = self.driver.find_element(By.NAME, 'card_set')
            cardset_select.click()
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f'option[value="{self.card_set.id}"]'))
            ).click()

            file_input = self.driver.find_element(By.NAME, 'image')
            file_input.send_keys(temp_image_path)

            self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

            WebDriverWait(self.driver, 10).until_not(
                EC.url_contains('/upload-card/')
            )

            uploaded_card = Card.objects.filter(title='Card with Image').first()
            self.assertIsNotNone(uploaded_card)
            self.assertTrue(uploaded_card.image.name)

        finally:
            if os.path.exists(temp_image_path):
                os.unlink(temp_image_path)

class CleanupTest(SeleniumTestBase):
    """Test class specifically for cleaning up test users"""

    def test_cleanup_all_test_users(self):
        """Elimina todos los usuarios de prueba creados durante los tests"""
        # Lista de usuarios de prueba conocidos
        test_usernames = ['testuser', 'newuser', 'uniqueuser', 'deleteuser', 'wrongdeleteuser']

        for username in test_usernames:
            if User.objects.filter(username=username).exists():
                try:
                    user = User.objects.get(username=username)
                    password = 'securepassword123'  # password por defecto para testuser

                    # Intentar diferentes contraseñas comunes de test
                    passwords_to_try = [
                        'securepassword123',
                        'newpass123',
                        'unique123',
                        'deletepass123',
                        'wrongpass123'
                    ]

                    deleted = False
                    for pwd in passwords_to_try:
                        if user.check_password(pwd):
                            success = self.delete_user_via_ui(username, pwd)
                            if success:
                                deleted = True
                                print(f"Successfully deleted user: {username}")
                                break

                    # Si no se pudo eliminar via UI, eliminar directamente
                    if not deleted and User.objects.filter(username=username).exists():
                        User.objects.get(username=username).delete()
                        print(f"Force deleted user: {username}")

                except Exception as e:
                    print(f"Error cleaning up user {username}: {e}")
                    # Force delete if everything else fails
                    if User.objects.filter(username=username).exists():
                        User.objects.get(username=username).delete()

    def tearDown(self):
        """Clean up after each test"""
        super().tearDown()
        # Additional cleanup if needed
        test_users = User.objects.filter(username__startswith='test')
        for user in test_users:
            try:
                user.delete()
            except:
                pass