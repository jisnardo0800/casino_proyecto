import unittest
from app import es_color  # Asegúrate de que app.py esté en el PYTHONPATH

class TestRuleta(unittest.TestCase):

    def test_color_rojo(self):
        """Número 3 debería ser rojo."""
        self.assertEqual(es_color(3), 'rojo')

    def test_color_negro(self):
        """Número 6 debería ser negro."""
        self.assertEqual(es_color(6), 'negro')

    def test_color_nulo(self):
        """Número 0 no tiene color."""
        self.assertEqual(es_color(0), 'ninguno')

    def test_color_borde(self):
        """Prueba un número límite, por ejemplo 36."""
        self.assertEqual(es_color(36), 'rojo')

    def test_color_fuera_rango(self):
        """Un número negativo o fuera de 0–36 podría considerarse ninguno."""
        self.assertEqual(es_color(-1), 'ninguno')
        self.assertEqual(es_color(37), 'ninguno')

if __name__ == '__main__':
    unittest.main()
