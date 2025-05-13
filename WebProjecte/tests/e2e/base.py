# Archivo: WebProjecte/tests/e2e/base.py
import os
import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from WebProjecte.models import Card, Rarity, CardSet, Profile, Collection


class SeleniumTestBase(StaticLiveServerTestCase):
    """Clase base para pruebas con Selenium"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Configurar opciones de Chrome para headless (sin interfaz gráfica)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Inicializar el WebDriver
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
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
        # Crear perfil para el usuario de prueba
        self.test_profile = Profile.objects.create(user=self.test_user)

        # Crear colección para el usuario de prueba
        self.test_collection = Collection.objects.create(user=self.test_user)

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
            image_url='https://example.com/base-set.jpg'
        )

        # Crear carta de prueba
        self.test_card = Card.objects.create(
            title='Test Card',
            description='This is a test card',
            image_url='https://example.com/test-card.jpg',
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