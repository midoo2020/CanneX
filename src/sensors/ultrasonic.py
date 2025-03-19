"""
Module pour la gestion du capteur ultrasonique HC-SR04.
Ce module permet de mesurer la distance avec un obstacle.
"""

import time
import logging
import RPi.GPIO as GPIO

# Configuration du logger
logger = logging.getLogger(__name__)

class UltrasonicSensor:
    """Classe pour gérer le capteur ultrasonique HC-SR04."""
    
    def __init__(self, trig_pin, echo_pin, max_distance=300):
        """
        Initialise le capteur ultrasonique.
        
        Args:
            trig_pin (int): Numéro de la broche GPIO pour le trigger
            echo_pin (int): Numéro de la broche GPIO pour l'echo
            max_distance (int): Distance maximale de détection en cm
        """
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.max_distance = max_distance
        
        # Configuration des broches GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trig_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        
        # S'assurer que le trigger est désactivé
        GPIO.output(self.trig_pin, False)
        time.sleep(0.5)  # Temps de stabilisation
        
        logger.info(f"Capteur ultrasonique initialisé (Trig: {trig_pin}, Echo: {echo_pin})")
    
    def measure_distance(self):
        """
        Mesure la distance avec un obstacle.
        
        Returns:
            float: Distance en centimètres, ou None si la mesure a échoué
        """
        # Envoyer une impulsion ultrasonique
        GPIO.output(self.trig_pin, False)
        time.sleep(0.01)
        GPIO.output(self.trig_pin, True)
        time.sleep(0.00001)  # 10 microsecondes
        GPIO.output(self.trig_pin, False)
        
        # Mesurer le temps entre l'envoi et la réception
        pulse_start = time.time()
        timeout_start = time.time()
        
        # Attendre le début de l'écho (signal passe à HIGH)
        while GPIO.input(self.echo_pin) == 0:
            pulse_start = time.time()
            # Gestion du timeout (capteur déconnecté ou défaillant)
            if time.time() - timeout_start > 0.1:  # 100ms de timeout
                logger.warning("Timeout en attendant le début de l'écho")
                return None
        
        # Attendre la fin de l'écho (signal passe à LOW)
        pulse_end = time.time()
        timeout_start = time.time()
        while GPIO.input(self.echo_pin) == 1:
            pulse_end = time.time()
            # Gestion du timeout (objet trop loin ou capteur défaillant)
            if time.time() - timeout_start > 0.1:  # 100ms de timeout
                logger.warning("Timeout en attendant la fin de l'écho")
                return None
        
        # Calculer la durée de l'impulsion
        pulse_duration = pulse_end - pulse_start
        
        # La vitesse du son est de 343 m/s, soit 34300 cm/s
        # Comme le son fait un aller-retour, on divise par 2
        # Distance = (Temps × Vitesse) ÷ 2
        distance = pulse_duration * 17150  # 34300 / 2
        
        # Arrondir à 2 décimales
        distance = round(distance, 2)
        
        # Vérifier que la distance est valide
        if distance > self.max_distance:
            logger.debug(f"Distance mesurée ({distance} cm) supérieure à max_distance ({self.max_distance} cm)")
            return self.max_distance
        
        logger.debug(f"Distance mesurée: {distance} cm")
        return distance
    
    def cleanup(self):
        """Nettoie les ressources GPIO utilisées."""
        # Ne pas nettoyer GPIO ici pour éviter d'affecter d'autres composants
        # GPIO.cleanup() sera appelé par le programme principal
        logger.info("Nettoyage des ressources du capteur ultrasonique")


def test_sensor():
    """Fonction de test pour le capteur ultrasonique."""
    try:
        # Configuration du logging pour le test
        logging.basicConfig(level=logging.INFO)
        
        # Initialiser le capteur avec les broches par défaut
        sensor = UltrasonicSensor(23, 24)
        
        print("Test du capteur ultrasonique. Appuyez sur Ctrl+C pour arrêter.")
        
        # Effectuer des mesures en continu
        while True:
            distance = sensor.measure_distance()
            if distance is not None:
                print(f"Distance: {distance} cm")
            else:
                print("Erreur de mesure")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur")
    finally:
        GPIO.cleanup()
        print("GPIO nettoyé")


if __name__ == "__main__":
    test_sensor() 