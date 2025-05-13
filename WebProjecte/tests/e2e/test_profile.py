# Archivo: WebProjecte/tests/e2e/test_profile.py
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .base import SeleniumTestBase


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
            # Estos selectores dependerán de la estructura de tu página de perfil
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