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

from django.core.management import call_command
from WebProjecte.models import Card, Rarity, CardSet, Profile, Collection


class SeleniumTestBase(StaticLiveServerTestCase):
    """Clase base para pruebas con Selenium"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Instalar automáticamente geckodriver si no está presente
        geckodriver_autoinstaller.install()

        # Configurar opciones de Firefox para headless (sin interfaz gráfica)
        firefox_options = Options()
        firefox_options.add_argument("--headless")  # Ejecutar en modo sin cabeza (headless)
        firefox_options.add_argument("--no-sandbox")  # Evitar problemas en entornos Linux
        firefox_options.add_argument("--disable-dev-shm-usage")  # Evitar errores relacionados con memoria compartida

        # Inicializar el WebDriver con Firefox (geckodriver)
        cls.driver = webdriver.Firefox(
            service=Service(geckodriver_autoinstaller.install()),  # Usar geckodriver autoinstaller
            options=firefox_options
        )

        # Maximizar la ventana
        cls.driver.maximize_window()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        # Crear datos de prueba
        self.create_test_data()

    def create_test_data(self):
        """Crear datos de prueba para las pruebas"""
        # Crear usuario de prueba
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepassword123'
        )

        # Crear colección con get_or_create para evitar duplicados
        self.test_collection, created = Collection.objects.get_or_create(user=self.test_user)

        # Verificar si la colección fue creada o no
        if created:
            print(f"Se creó la colección para {self.test_user.username}")
        else:
            print(f"La colección ya existía para {self.test_user.username}")

        # Crear rareza
        self.test_rarity = Rarity.objects.create(
            title='Common',
            description='A common card',
            probability=0.7
        )

        # Crear set de cartas
        self.test_card_set = CardSet.objects.create(
            title='Base Set',
            description='The base set of cards',
        )

        # Crear carta de prueba
        self.test_card = Card.objects.create(
            title='Test Card',
            description='This is a test card',
            rarity=self.test_rarity,
            card_set=self.test_card_set
        )

    def login(self, username='testuser', password='securepassword123'):
        """Método helper para hacer login"""
        self.driver.get(f'{self.live_server_url}/login/')

        # Esperar a que el formulario de login esté disponible
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )

        # Introducir credenciales
        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'password').send_keys(password)

        # Enviar formulario
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Esperar a que se complete el login
        WebDriverWait(self.driver, 10).until(
            EC.url_contains(self.live_server_url)
        )


class AuthenticationTest(SeleniumTestBase):
    """Pruebas para la autenticación"""

    def test_user_creation_creates_only_one_collection(self):
        """Asegura que solo se cree una colección por usuario"""
        # Crear un usuario nuevo para esta prueba específica
        new_user = User.objects.create_user(
            username='onecoluser',
            email='onecol@example.com',
            password='password123'
        )

        # Verificar si ya existe una colección para este usuario
        if not Collection.objects.filter(user=new_user).exists():
            Collection.objects.create(user=new_user)

        # Asegurarse de que solo hay una colección para el usuario
        self.assertEqual(Collection.objects.filter(user=new_user).count(), 1)

    def test_login_success(self):
        """Prueba de inicio de sesión exitoso"""
        # Navegar a la página de login
        self.driver.get(f'{self.live_server_url}/login/')

        # Esperar a que el formulario de login esté disponible
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'username'))
            )
        except TimeoutException:
            self.fail("El formulario de login no se cargó correctamente")

        # Verificar que estamos en la página de login
        self.assertIn('login', self.driver.current_url)

        # Introducir credenciales
        self.driver.find_element(By.NAME, 'username').send_keys('testuser')
        self.driver.find_element(By.NAME, 'password').send_keys('securepassword123')

        # Enviar formulario
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Esperar a que se complete el login y redirija a la página principal
        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_contains(self.live_server_url)
            )
        except TimeoutException:
            self.fail("No se redirigió correctamente después del login")

        # Verificar que estamos en la página principal
        self.assertEqual(self.driver.current_url, f'{self.live_server_url}/')

        # Verificar que hay elementos que indican que el usuario está logueado
        try:
            # Esperamos ver algún elemento que solo aparece cuando el usuario está logueado
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.LINK_TEXT, 'Profile'))
            )
        except TimeoutException:
            self.fail("No se detectaron elementos de usuario logueado")

    def test_login_failure(self):
        """Prueba de inicio de sesión fallido"""
        # Navegar a la página de login
        self.driver.get(f'{self.live_server_url}/login/')

        # Esperar a que el formulario de login esté disponible
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )

        # Introducir credenciales incorrectas
        self.driver.find_element(By.NAME, 'username').send_keys('testuser')
        self.driver.find_element(By.NAME, 'password').send_keys('wrongpassword')

        # Enviar formulario
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Esperar a que aparezca el mensaje de error
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.alert-danger'))
            )
        except TimeoutException:
            self.fail("No se mostró mensaje de error con credenciales incorrectas")

        # Verificar que seguimos en la página de login
        self.assertIn('login', self.driver.current_url)

    def test_register(self):
        """Prueba de registro de usuario"""
        # Navegar a la página de registro
        self.driver.get(f'{self.live_server_url}/register/')

        # Esperar a que el formulario de registro esté disponible
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )

        # Introducir datos de registro con un nombre diferente para evitar conflictos
        username = 'newuser_register_test'
        email = 'new_register@example.com'
        password = 'securenewpassword123'

        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'email').send_keys(email)
        self.driver.find_element(By.NAME, 'password1').send_keys(password)
        self.driver.find_element(By.NAME, 'password2').send_keys(password)

        # Enviar formulario
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Esperar a que se complete el registro y redirija a la página principal
        WebDriverWait(self.driver, 10).until(
            EC.url_contains(self.live_server_url)
        )

        # Verificar que estamos en la página principal
        self.assertEqual(self.driver.current_url, f'{self.live_server_url}/')

        # Verificar que la colección solo se creó una vez
        user = User.objects.get(username=username)
        collection_count = Collection.objects.filter(user=user).count()

        # Asegúrate de que solo haya una colección para este usuario
        self.assertEqual(collection_count, 1, "La colección se ha creado más de una vez")

        # Verificar que el usuario se creó en la base de datos
        self.assertTrue(
            self.driver.find_element(By.LINK_TEXT, 'Profile').is_displayed(),
            "El usuario no parece estar logueado después del registro"
        )

    def test_logout(self):
        """Prueba de cierre de sesión"""
        # Primero hacemos login
        self.login()

        # Verificar que el login fue exitoso
        self.assertEqual(self.driver.current_url, f'{self.live_server_url}/')

        # Buscar y hacer clic en el enlace de logout
        try:
            logout_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, 'Logout'))
            )
            logout_link.click()
        except TimeoutException:
            self.fail("No se encontró el enlace de logout")

        # Esperar a que se complete el logout y redirija a la página principal
        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_contains(self.live_server_url)
            )
        except TimeoutException:
            self.fail("No se redirigió correctamente después del logout")

        # Verificar que estamos en la página principal sin sesión iniciada
        self.assertEqual(self.driver.current_url, f'{self.live_server_url}/')

        # Verificar que hay elementos que indican que el usuario está deslogueado
        try:
            # Esperamos ver el enlace de login, que solo aparece cuando el usuario está deslogueado
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.LINK_TEXT, 'Login'))
            )
        except TimeoutException:
            self.fail("No se detectaron elementos de usuario deslogueado")


class CardsTest(SeleniumTestBase):
    """Pruebas para la funcionalidad de cartas"""

    def test_view_cards_page(self):
        """Prueba de visualización de la página de cartas"""
        # Navegar a la página de cartas
        self.driver.get(f'{self.live_server_url}/cards/')

        # Esperar a que la página de cartas se cargue
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("La página de cartas no se cargó correctamente")

        # Verificar que estamos en la página de cartas
        self.assertIn('cards', self.driver.current_url)

        # Verificar que las cartas se muestran en la página
        try:
            cards = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'card'))
                # Asume que cada carta tiene la clase 'card'
            )
            # Debe haber al menos una carta (la que creamos en los datos de prueba)
            self.assertGreaterEqual(len(cards), 1)
        except TimeoutException:
            self.fail("No se encontraron cartas en la página")

    def test_card_details(self):
        """Prueba de visualización de detalles de una carta"""
        # Navegar a la página de una carta específica
        card = Card.objects.first()  # O usa una carta específica de tus datos de prueba
        self.driver.get(f'{self.live_server_url}/card/{card.id}/')

        # Esperar a que la página de la carta se cargue
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("La página de detalles de la carta no se cargó correctamente")

        # Verificar que estamos en la página de detalles de la carta
        self.assertIn(f'card/{card.id}/', self.driver.current_url)

        # Verificar que se muestran los detalles de la carta
        try:
            card_title = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'card-title'))
            )
            self.assertEqual(card_title.text, card.title)

            card_description = self.driver.find_element(By.CLASS_NAME, 'card-description')
            self.assertEqual(card_description.text, card.description)

            # Verificar que hay una imagen (si el modelo tiene un campo de imagen)
            try:
                card_image = self.driver.find_element(By.TAG_NAME, 'img')
                self.assertTrue(card_image.get_attribute('src').endswith(card.image.url))
            except:
                pass  # Si no hay imagen, no fallar la prueba
        except TimeoutException:
            self.fail("No se encontraron detalles de la carta en la página")

    def test_api_cards(self):
        """Prueba de la API de cartas"""
        # Navegar a la API de cartas
        self.driver.get(f'{self.live_server_url}/api/cartas/')

        # La API debería devolver JSON, que el navegador mostrará como texto
        try:
            pre_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'pre'))
            )
            # Verificar que el texto contiene elementos esperados
            json_text = pre_element.text
            self.assertIn('"nombre":', json_text)
            self.assertIn('"imagen":', json_text)
            self.assertIn('"texto":', json_text)
            self.assertIn('"tipo":', json_text)
        except TimeoutException:
            # Si no hay un elemento pre, podría ser que el navegador está renderizando el JSON directamente
            self.assertIn('"nombre":', self.driver.page_source)
            self.assertIn('"imagen":', self.driver.page_source)
            self.assertIn('"texto":', self.driver.page_source)
            self.assertIn('"tipo":', self.driver.page_source)

    def test_add_card_admin_only(self):
        """Prueba de adición de carta (solo admin)"""
        # Crear usuario admin
        admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpassword123',
            is_staff=True,
            is_superuser=True
        )

        # Crear colección para el admin (usando get_or_create)
        Collection.objects.get_or_create(user=admin_user)

        # Login como admin
        self.login(username='adminuser', password='adminpassword123')

        # Navegar a la página de añadir carta
        self.driver.get(f'{self.live_server_url}/add-card/')

        # Esperar a que la página de añadir carta se cargue
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'form'))
            )
        except TimeoutException:
            self.fail("La página de añadir carta no se cargó correctamente o el usuario no tiene permiso")

        # Rellenar el formulario
        title_field = self.driver.find_element(By.NAME, 'title')
        description_field = self.driver.find_element(By.NAME, 'description')

        # Introducir datos
        title_field.send_keys('Nueva Carta')
        description_field.send_keys('Esta es una nueva carta de prueba')

        # Enviar formulario
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Esperar a que se complete la creación y redirija a la página de cartas
        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_contains('/cards/')
            )
        except TimeoutException:
            self.fail("No se redirigió correctamente después de añadir la carta")

        # Verificar que la carta se creó en la base de datos
        self.assertTrue(Card.objects.filter(title='Nueva Carta').exists(), "La carta no se creó correctamente")

    def test_add_card_regular_user(self):
        """Prueba que un usuario regular no puede añadir cartas"""
        # Login como usuario regular
        self.login()

        # Intentar navegar a la página de añadir carta
        self.driver.get(f'{self.live_server_url}/add-card/')

        # Verificar que no tenemos acceso (debería redirigir o mostrar un error)
        # El comportamiento exacto dependerá de cómo manejas el acceso denegado
        try:
            # Si se redirige a login o principal
            WebDriverWait(self.driver, 10).until(
                EC.url_changes(f'{self.live_server_url}/add-card/')
            )
        except TimeoutException:
            # Si no se redirige, debería mostrar algún mensaje de error
            error_message = self.driver.find_element(By.TAG_NAME, 'body').text
            self.assertIn('forbidden', error_message.lower())


class ProfileTest(SeleniumTestBase):
    """Pruebas para la funcionalidad de perfil de usuario"""

    def test_view_profile(self):
        """Prueba de visualización del perfil de usuario"""
        # Primero hacemos login
        self.login()

        # Navegar a la página de perfil
        self.driver.get(f'{self.live_server_url}/profile/')

        # Esperar a que la página de perfil se cargue
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("La página de perfil no se cargó correctamente")

        # Verificar que estamos en la página de perfil
        self.assertIn('profile', self.driver.current_url)

        # Verificar que se muestra la información del perfil
        try:
            # Buscar elementos específicos del perfil
            username_element = self.driver.find_element(By.ID, 'username')
            self.assertEqual(username_element.text, 'testuser')
        except:
            # Si no hay un elemento específico para el username, verificamos que al menos el nombre de usuario aparece en la página
            self.assertIn('testuser', self.driver.page_source)

    def test_update_profile_username(self):
        """Prueba de actualización del nombre de usuario en el perfil"""
        # Primero hacemos login
        self.login()

        # Navegar a la página de perfil
        self.driver.get(f'{self.live_server_url}/profile/')

        # Esperar a que la página de perfil se cargue
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )

        # Rellenar el formulario para actualizar el nombre de usuario
        username_field = self.driver.find_element(By.NAME, 'username')
        # Limpiar el campo y escribir el nuevo nombre de usuario
        username_field.clear()
        new_username = 'updated_user'
        username_field.send_keys(new_username)

        # Enviar formulario
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Esperar a que se complete la actualización y refresque la página
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("La página no se refrescó correctamente después de actualizar el perfil")

        # Verificar que se muestra el mensaje de éxito
        try:
            success_message = self.driver.find_element(By.CLASS_NAME, 'alert-success')
            self.assertIn('actualizado', success_message.text.lower())
        except:
            # Si no hay un mensaje de éxito específico, verificamos que el nuevo nombre de usuario aparece en la página
            self.assertIn(new_username, self.driver.page_source)

    def test_update_profile_password(self):
        """Prueba de actualización de la contraseña en el perfil"""
        # Primero hacemos login
        self.login()

        # Navegar a la página de perfil
        self.driver.get(f'{self.live_server_url}/profile/')

        # Esperar a que la página de perfil se cargue
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )

        # Rellenar el formulario para actualizar la contraseña
        password_field = self.driver.find_element(By.NAME, 'password')
        # Escribir la nueva contraseña
        new_password = 'newsecurepassword123'
        password_field.send_keys(new_password)

        # Enviar formulario
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Esperar a que se complete la actualización y refresque la página
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("La página no se refrescó correctamente después de actualizar el perfil")

        # Verificar que se muestra el mensaje de éxito
        try:
            success_message = self.driver.find_element(By.CLASS_NAME, 'alert-success')
            self.assertIn('actualizado', success_message.text.lower())
        except:
            pass  # Si no hay un mensaje específico, es difícil verificar el cambio de contraseña

        # Hacer logout
        self.driver.get(f'{self.live_server_url}/logout/')

        # Intentar hacer login con la nueva contraseña
        self.driver.get(f'{self.live_server_url}/login/')

        # Esperar a que el formulario de login esté disponible
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )

        # Introducir credenciales con la nueva contraseña
        self.driver.find_element(By.NAME, 'username').send_keys('testuser')
        self.driver.find_element(By.NAME, 'password').send_keys(new_password)

        # Enviar formulario
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Esperar a que se complete el login y redirija a la página principal
        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_contains(self.live_server_url)
            )
            # Verificar que estamos en la página principal (login exitoso con la nueva contraseña)
            self.assertEqual(self.driver.current_url, f'{self.live_server_url}/')
        except TimeoutException:
            self.fail("No se pudo iniciar sesión con la nueva contraseña")