import os
import time
import geckodriver_autoinstaller
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from WebProjecte.models import Card, Rarity, CardSet, Profile, Collection

from django.core.management import call_command


def setUp(self):
    """Limpiar la base de datos antes de cada prueba y crear datos de prueba"""
    call_command('flush', interactive=False)
    self.create_test_data()


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
            EC.presence_of_element_located(('name', 'username'))
        )

        # Introducir credenciales
        self.driver.find_element('name', 'username').send_keys(username)
        self.driver.find_element('name', 'password').send_keys(password)

        # Enviar formulario
        self.driver.find_element('css selector', 'button[type="submit"]').click()

        # Esperar a que se complete el login
        WebDriverWait(self.driver, 10).until(
            EC.url_contains(self.live_server_url)
        )