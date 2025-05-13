# Archivo: WebProjecte/tests/e2e/test_authentication.py
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .base import SeleniumTestBase


class AuthenticationTest(SeleniumTestBase):
    """Pruebas para la autenticación"""

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
            # Esto dependerá de tu implementación específica, pero podría ser un botón de perfil o similar
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
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'username'))
            )
        except TimeoutException:
            self.fail("El formulario de registro no se cargó correctamente")

        # Introducir datos de registro
        username = 'newuser'
        email = 'new@example.com'
        password = 'securenewpassword123'

        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'email').send_keys(email)
        self.driver.find_element(By.NAME, 'password1').send_keys(password)
        self.driver.find_element(By.NAME, 'password2').send_keys(password)

        # Enviar formulario
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Esperar a que se complete el registro y redirija a la página principal
        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_contains(self.live_server_url)
            )
        except TimeoutException:
            self.fail("No se redirigió correctamente después del registro")

        # Verificar que estamos en la página principal
        self.assertEqual(self.driver.current_url, f'{self.live_server_url}/')

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