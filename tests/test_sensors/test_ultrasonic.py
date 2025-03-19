"""
Tests unitaires pour le module du capteur ultrasonique.
"""

import unittest
from unittest.mock import patch, MagicMock
import time
import RPi.GPIO as GPIO
from src.sensors.ultrasonic import UltrasonicSensor

class TestUltrasonicSensor(unittest.TestCase):
    """Tests pour la classe UltrasonicSensor."""
    
    @patch('RPi.GPIO.setup')
    @patch('RPi.GPIO.output')
    @patch('RPi.GPIO.setmode')
    def setUp(self, mock_setmode, mock_output, mock_setup):
        """Configuration avant chaque test."""
        self.trig_pin = 23
        self.echo_pin = 24
        self.max_distance = 200
        
        # Créer une instance du capteur avec des broches GPIO simulées
        self.sensor = UltrasonicSensor(
            self.trig_pin, self.echo_pin, self.max_distance
        )
    
    @patch('RPi.GPIO.output')
    @patch('RPi.GPIO.input')
    @patch('time.time')
    def test_measure_distance_normal(self, mock_time, mock_input, mock_output):
        """Teste la mesure de distance dans un cas normal."""
        # Simuler le timing pour une distance de 50 cm
        # Distance = (Temps * Vitesse) / 2
        # Pour 50 cm: Temps = (2 * Distance) / Vitesse = (2 * 50) / 34300 = 0.00292 secondes
        
        # Configurer les mocks pour simuler le fonctionnement du capteur
        pulse_duration = 0.00292  # Pour 50cm
        
        # Simuler les temps retournés par time.time()
        mock_time.side_effect = [
            0.0,      # Premier appel (timeout_start)
            0.001,    # Deuxième appel (pulse_start)
            0.001,    # Troisième appel (timeout_start)
            0.00392   # Quatrième appel (pulse_end = pulse_start + pulse_duration)
        ]
        
        # Simuler les états de la broche d'écho (d'abord 0, puis 1)
        mock_input.side_effect = [0, 1, 1, 0]
        
        # Appeler la méthode à tester
        distance = self.sensor.measure_distance()
        
        # Vérifier que la distance calculée est proche de 50 cm (avec une petite marge d'erreur)
        self.assertAlmostEqual(distance, 50.0, delta=0.5)
        
        # Vérifier que les méthodes GPIO ont été appelées correctement
        mock_output.assert_any_call(self.trig_pin, False)
        mock_output.assert_any_call(self.trig_pin, True)
    
    @patch('RPi.GPIO.output')
    @patch('RPi.GPIO.input')
    @patch('time.time')
    def test_measure_distance_timeout(self, mock_time, mock_input, mock_output):
        """Teste le timeout lors de la mesure."""
        # Simuler un timeout (le signal reste à 0)
        
        # Configurer time.time() pour incrémenter de 0.2s à chaque appel (> timeout de 0.1s)
        mock_time.side_effect = [0.0, 0.2]
        
        # Simuler un capteur qui ne répond pas (écho reste toujours à 0)
        mock_input.return_value = 0
        
        # Appeler la méthode à tester
        distance = self.sensor.measure_distance()
        
        # Vérifier que la mesure renvoie None en cas de timeout
        self.assertIsNone(distance)
    
    @patch('RPi.GPIO.output')
    @patch('RPi.GPIO.input')
    @patch('time.time')
    def test_measure_distance_max_range(self, mock_time, mock_input, mock_output):
        """Teste la mesure quand la distance dépasse la valeur maximale configurée."""
        # Simuler une distance très grande (500 cm, au-delà du max_distance de 200 cm)
        
        # Configurer les mocks pour simuler le fonctionnement du capteur
        pulse_duration = 0.0292  # Pour 500cm
        
        mock_time.side_effect = [
            0.0,      # Premier appel
            0.001,    # Deuxième appel
            0.001,    # Troisième appel
            0.0302    # Quatrième appel (0.001 + pulse_duration)
        ]
        
        mock_input.side_effect = [0, 1, 1, 0]
        
        # Appeler la méthode à tester
        distance = self.sensor.measure_distance()
        
        # Vérifier que la distance est limitée à max_distance
        self.assertEqual(distance, self.max_distance)

if __name__ == '__main__':
    unittest.main() 