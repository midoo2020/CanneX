"""
Module pour la gestion des retours haptiques (vibration).
"""

import time
import logging
import threading
import RPi.GPIO as GPIO

# Configuration du logger
logger = logging.getLogger(__name__)

class HapticFeedback:
    """Classe pour gérer les retours haptiques via un moteur de vibration."""
    
    def __init__(self, vibration_pin, enabled=True):
        """
        Initialise le module de retour haptique.
        
        Args:
            vibration_pin (int): Numéro de la broche GPIO pour le moteur de vibration
            enabled (bool): Activer/désactiver les retours haptiques
        """
        self.vibration_pin = vibration_pin
        self.enabled = enabled
        self.vibrating = False
        self.vibration_thread = None
        self.stop_event = threading.Event()
        
        # Configuration de la broche GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.vibration_pin, GPIO.OUT)
        
        # S'assurer que le moteur est désactivé au démarrage
        GPIO.output(self.vibration_pin, GPIO.LOW)
        
        logger.info(f"Module haptique initialisé (broche: {vibration_pin}, activé: {enabled})")
    
    def vibrate(self, duration=0.5, pattern=None):
        """
        Fait vibrer le moteur pendant une durée spécifiée.
        
        Args:
            duration (float): Durée de la vibration en secondes (ignoré si pattern est fourni)
            pattern (list): Liste de tuples (durée_on, durée_off) pour créer un motif de vibration
        """
        if not self.enabled:
            logger.debug("Vibration ignorée car le module est désactivé")
            return
        
        # Arrêter toute vibration en cours
        self.stop_vibration()
        
        # Réinitialiser l'événement d'arrêt
        self.stop_event.clear()
        
        # Démarrer la vibration dans un thread séparé
        if pattern:
            self.vibration_thread = threading.Thread(
                target=self._vibrate_pattern, 
                args=(pattern,)
            )
        else:
            self.vibration_thread = threading.Thread(
                target=self._vibrate_single, 
                args=(duration,)
            )
        
        self.vibration_thread.daemon = True
        self.vibration_thread.start()
        
        logger.debug(f"Vibration démarrée (durée: {duration}s, motif: {pattern is not None})")
    
    def _vibrate_single(self, duration):
        """
        Fonction interne pour une vibration simple.
        
        Args:
            duration (float): Durée de la vibration en secondes
        """
        try:
            self.vibrating = True
            GPIO.output(self.vibration_pin, GPIO.HIGH)
            
            # Attendre la durée spécifiée ou jusqu'à ce que stop_event soit défini
            self.stop_event.wait(timeout=duration)
            
            GPIO.output(self.vibration_pin, GPIO.LOW)
            self.vibrating = False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vibration: {e}")
            GPIO.output(self.vibration_pin, GPIO.LOW)
            self.vibrating = False
    
    def _vibrate_pattern(self, pattern):
        """
        Fonction interne pour une vibration avec motif.
        
        Args:
            pattern (list): Liste de tuples (durée_on, durée_off)
        """
        try:
            self.vibrating = True
            
            # Répéter le motif jusqu'à ce que stop_event soit défini
            while not self.stop_event.is_set():
                for on_time, off_time in pattern:
                    # Activer la vibration
                    GPIO.output(self.vibration_pin, GPIO.HIGH)
                    
                    # Attendre la durée d'activation ou jusqu'à stop_event
                    if self.stop_event.wait(timeout=on_time):
                        break
                    
                    # Désactiver la vibration
                    GPIO.output(self.vibration_pin, GPIO.LOW)
                    
                    # Attendre la durée de désactivation ou jusqu'à stop_event
                    if self.stop_event.wait(timeout=off_time):
                        break
                
                # Si on a atteint la fin du motif et qu'aucun arrêt n'a été demandé,
                # sortir de la boucle (le motif n'est joué qu'une fois)
                break
            
            # S'assurer que le moteur est désactivé
            GPIO.output(self.vibration_pin, GPIO.LOW)
            self.vibrating = False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vibration avec motif: {e}")
            GPIO.output(self.vibration_pin, GPIO.LOW)
            self.vibrating = False
    
    def stop_vibration(self):
        """Arrête toute vibration en cours."""
        if self.vibrating:
            # Signaler l'arrêt au thread de vibration
            self.stop_event.set()
            
            # Attendre que le thread se termine
            if self.vibration_thread and self.vibration_thread.is_alive():
                self.vibration_thread.join(timeout=0.5)
            
            # S'assurer que le moteur est désactivé
            GPIO.output(self.vibration_pin, GPIO.LOW)
            self.vibrating = False
            
            logger.debug("Vibration arrêtée")
    
    def vibrate_warning(self):
        """Vibration d'avertissement (motif court)."""
        pattern = [(0.2, 0.2), (0.2, 0.2)]
        self.vibrate(pattern=pattern)
    
    def vibrate_danger(self):
        """Vibration de danger (motif long et intense)."""
        pattern = [(0.5, 0.1), (0.5, 0.1), (0.5, 0.5)]
        self.vibrate(pattern=pattern)
    
    def vibrate_info(self):
        """Vibration d'information (motif court et doux)."""
        self.vibrate(duration=0.3)
    
    def cleanup(self):
        """Nettoie les ressources utilisées par le module haptique."""
        # Arrêter toute vibration en cours
        self.stop_vibration()
        
        # Ne pas nettoyer GPIO ici pour éviter d'affecter d'autres composants
        # GPIO.cleanup() sera appelé par le programme principal
        logger.info("Ressources du module haptique libérées")


def test_haptic():
    """Fonction de test pour le module haptique."""
    try:
        # Configuration du logging pour le test
        logging.basicConfig(level=logging.INFO)
        
        # Initialiser le module haptique avec la broche par défaut
        haptic = HapticFeedback(18)
        
        print("Test du module haptique. Appuyez sur Ctrl+C pour arrêter.")
        
        # Tester la vibration simple
        print("Test de vibration simple (1 seconde)...")
        haptic.vibrate(duration=1.0)
        time.sleep(2)
        
        # Tester les vibrations spécifiques
        print("Test de vibration d'information...")
        haptic.vibrate_info()
        time.sleep(2)
        
        print("Test de vibration d'avertissement...")
        haptic.vibrate_warning()
        time.sleep(2)
        
        print("Test de vibration de danger...")
        haptic.vibrate_danger()
        time.sleep(2)
        
        # Tester un motif personnalisé
        print("Test de motif personnalisé (SOS en morse)...")
        # SOS en morse: ... --- ...
        sos_pattern = [
            (0.2, 0.2), (0.2, 0.2), (0.2, 0.5),  # S (court-court-court)
            (0.5, 0.2), (0.5, 0.2), (0.5, 0.5),  # O (long-long-long)
            (0.2, 0.2), (0.2, 0.2), (0.2, 0.2)   # S (court-court-court)
        ]
        haptic.vibrate(pattern=sos_pattern)
        time.sleep(5)
        
        print("Test terminé.")
            
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur")
    finally:
        if 'haptic' in locals():
            haptic.cleanup()
        GPIO.cleanup()
        print("GPIO nettoyé")


if __name__ == "__main__":
    test_haptic() 