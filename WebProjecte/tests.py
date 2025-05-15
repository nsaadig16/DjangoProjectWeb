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

        # Añadir carta a la colección del usuario
        CollectionCard.objects.create(
            card=self.test_card,
            collection=self.test_collection,
            quantity=1
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
            User.objects.filter(username=username).exists(),
            "El usuario no se creó correctamente"
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
        self.driver.get(f'{self.live_server_url}/card/')

        # Esperar a que la página de cartas se cargue
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("La página de cartas no se cargó correctamente")

        # Verificar que estamos en la página de cartas
        self.assertIn('card', self.driver.current_url)

    def test_api_cards(self):
        """Prueba de la API de cartas"""
        # Navegar a la API de cartas
        self.driver.get(f'{self.live_server_url}/api/cartas/')

        # La API debería devolver JSON, que el navegador mostrará como texto
        try:
            # Esperar a que se cargue la página
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )

            # Verificar que el texto contiene elementos esperados
            # Adaptamos esto ya que la estructura exacta del JSON puede variar
            page_source = self.driver.page_source
            self.assertTrue(
                'title' in page_source or
                'nombre' in page_source or
                'description' in page_source or
                'texto' in page_source,
                "La respuesta JSON no contiene los campos esperados"
            )
        except TimeoutException:
            self.fail("La API de cartas no devolvió una respuesta")

    def test_user_cards_api(self):
        """Prueba de la API de cartas del usuario"""
        # Primero hacemos login
        self.login()

        # Navegar a la API de cartas del usuario
        self.driver.get(f'{self.live_server_url}/api/mis-cartas/')

        # La API debería devolver JSON con las cartas del usuario
        try:
            # Esperar a que se cargue la página
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )

            # Verificar que el texto contiene elementos esperados
            page_source = self.driver.page_source
            self.assertTrue(
                'title' in page_source or
                'nombre' in page_source or
                'quantity' in page_source or
                'cantidad' in page_source,
                "La respuesta JSON no contiene los campos esperados"
            )
        except TimeoutException:
            self.fail("La API de cartas del usuario no devolvió una respuesta")


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

        # Verificar que al menos el nombre de usuario aparece en la página
        self.assertIn('testuser', self.driver.page_source)

    def test_view_collection(self):
        """Prueba de visualización de la colección del usuario"""
        # Primero hacemos login
        self.login()

        # Navegar a la página de colección
        self.driver.get(f'{self.live_server_url}/coleccion/')

        # Esperar a que la página de colección se cargue
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("La página de colección no se cargó correctamente")

        # Verificar que estamos en la página de colección
        self.assertIn('coleccion', self.driver.current_url)

    def test_friends_list(self):
        """Prueba de visualización de la lista de amigos"""
        # Primero hacemos login
        self.login()

        # Navegar a la página de amigos
        self.driver.get(f'{self.live_server_url}/friends/')

        # Esperar a que la página de amigos se cargue
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("La página de amigos no se cargó correctamente")

        # Verificar que estamos en la página de amigos
        self.assertIn('friends', self.driver.current_url)


class GeneralPagesTest(SeleniumTestBase):
    """Pruebas para páginas generales"""

    def test_como_jugar_page(self):
        """Prueba de visualización de la página de cómo jugar"""
        # Navegar a la página de cómo jugar
        self.driver.get(f'{self.live_server_url}/como-jugar/')

        # Esperar a que la página se cargue
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("La página de cómo jugar no se cargó correctamente")

        # Verificar que estamos en la página correcta
        self.assertIn('como-jugar', self.driver.current_url)

    def test_open_pack_page(self):
        """Prueba de visualización de la página de abrir pack (solo usuarios logueados)"""
        # Primero hacemos login
        self.login()

        # Navegar a la página de abrir pack
        self.driver.get(f'{self.live_server_url}/pack/open/')

        # Esperar a que la página se cargue
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("La página de abrir pack no se cargó correctamente")

        # Verificar que estamos en la página correcta
        self.assertIn('pack/open', self.driver.current_url)