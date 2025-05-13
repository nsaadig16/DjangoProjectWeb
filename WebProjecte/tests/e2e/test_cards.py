# Archivo: WebProjecte/tests/e2e/test_cards.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from django.contrib.auth.models import User
from WebProjecte.models import Card

from .base import SeleniumTestBase


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
        self.driver.get(f'{self.live_server_url}/card/')

        # Esperar a que la página de la carta se cargue
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            self.fail("La página de detalles de la carta no se cargó correctamente")

        # Verificar que estamos en la página de detalles de la carta
        self.assertIn('card', self.driver.current_url)

        # Verificar que se muestran los detalles de la carta
        # Esto dependerá de la estructura de tu página de detalles
        try:
            # Aquí deberías buscar elementos específicos que muestren los detalles de la carta
            # Por ejemplo, título, descripción, imagen, etc.
            card_title = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'card-title'))
                # Asume que el título tiene la clase 'card-title'
            )
            self.assertIsNotNone(card_title)
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
            self.assertIn('nombre', json_text)
            self.assertIn('imagen', json_text)
            self.assertIn('texto', json_text)
            self.assertIn('tipo', json_text)
        except TimeoutException:
            # Si no hay un elemento pre, podría ser que el navegador está renderizando el JSON directamente
            self.assertIn('"nombre":', self.driver.page_source)
            self.assertIn('"imagen":', self.driver.page_source)

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

        # Verificar que estamos en la página de añadir carta
        self.assertIn('add-card', self.driver.current_url)

        # Rellenar el formulario
        # Nota: Los nombres de campo dependerán de tu implementación específica
        title_field = self.driver.find_element(By.NAME, 'title')
        description_field = self.driver.find_element(By.NAME, 'description')
        image_url_field = self.driver.find_element(By.NAME, 'image_url')

        # Seleccionar rareza y set (los valores dependerán de tus datos)
        rarity_select = self.driver.find_element(By.NAME, 'rarity')
        card_set_select = self.driver.find_element(By.NAME, 'card_set')

        # Introducir datos
        title_field.send_keys('Nueva Carta')
        description_field.send_keys('Esta es una nueva carta de prueba')
        image_url_field.send_keys('https://example.com/nueva-carta.jpg')

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
        self.assertTrue(Card.objects.filter(title='Nueva Carta').exists())

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