"""
Module pour la gestion des retours audio et de la synthèse vocale.
Utilise gTTS pour la synthèse vocale et pygame pour la lecture audio.
"""

import os
import time
import logging
import tempfile
import threading
import pygame
from gtts import gTTS

# Configuration du logger
logger = logging.getLogger(__name__)

class AudioFeedback:
    """Classe pour gérer les retours audio et la synthèse vocale."""
    
    def __init__(self, language='fr', volume=1.0, speech_rate=1.0):
        """
        Initialise le module de retour audio.
        
        Args:
            language (str): Langue utilisée pour la synthèse vocale
            volume (float): Volume audio (0.0 à 1.0)
            speech_rate (float): Vitesse de parole (0.5 à 2.0)
        """
        self.language = language
        self.volume = volume
        self.speech_rate = speech_rate
        self.temp_dir = tempfile.gettempdir()
        self.speaking = False
        self.speech_queue = []
        self.queue_lock = threading.Lock()
        self.speech_thread = None
        
        # Initialiser pygame pour la lecture audio
        pygame.mixer.init()
        pygame.init()
        
        logger.info(f"Module audio initialisé (langue: {language}, volume: {volume})")
    
    def _speak_worker(self):
        """Fonction de travail pour le thread de parole."""
        while True:
            # Récupérer un message de la file d'attente
            with self.queue_lock:
                if not self.speech_queue:
                    self.speaking = False
                    break
                text = self.speech_queue.pop(0)
            
            # Générer et lire la synthèse vocale
            self._generate_and_play_speech(text)
    
    def _generate_and_play_speech(self, text):
        """
        Génère et lit un message vocal.
        
        Args:
            text (str): Texte à synthétiser et lire
        """
        try:
            # Générer la synthèse vocale avec gTTS
            tts = gTTS(text=text, lang=self.language, slow=(self.speech_rate < 1.0))
            
            # Créer un fichier temporaire pour la synthèse
            filename = os.path.join(self.temp_dir, f"canne_speech_{int(time.time())}.mp3")
            tts.save(filename)
            
            # Lire le fichier audio
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            # Attendre la fin de la lecture
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # Supprimer le fichier temporaire
            os.remove(filename)
            
            logger.debug(f"Message vocal lu: {text}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la synthèse vocale: {e}")
    
    def speak(self, text, priority=False):
        """
        Ajoute un message à la file d'attente de synthèse vocale.
        
        Args:
            text (str): Texte à synthétiser
            priority (bool): Si True, le message est ajouté en tête de file
        """
        # Ignorer les messages vides
        if not text:
            return
        
        with self.queue_lock:
            # Ajouter le message à la file d'attente
            if priority:
                self.speech_queue.insert(0, text)
            else:
                self.speech_queue.append(text)
            
            # Démarrer le thread de parole s'il n'est pas déjà en cours
            if not self.speaking:
                self.speaking = True
                self.speech_thread = threading.Thread(target=self._speak_worker)
                self.speech_thread.daemon = True
                self.speech_thread.start()
        
        logger.debug(f"Message ajouté à la file d'attente: {text} (priorité: {priority})")
    
    def play_sound(self, sound_type):
        """
        Joue un son d'alerte prédéfini.
        
        Args:
            sound_type (str): Type de son à jouer ('warning', 'danger', 'info')
        """
        try:
            sound_file = None
            
            # Sélectionner le fichier son en fonction du type
            if sound_type == 'warning':
                sound_file = os.path.join(os.path.dirname(__file__), '..', '..', 'sounds', 'warning.wav')
            elif sound_type == 'danger':
                sound_file = os.path.join(os.path.dirname(__file__), '..', '..', 'sounds', 'danger.wav')
            elif sound_type == 'info':
                sound_file = os.path.join(os.path.dirname(__file__), '..', '..', 'sounds', 'info.wav')
            
            # Vérifier si le fichier existe
            if sound_file and os.path.exists(sound_file):
                sound = pygame.mixer.Sound(sound_file)
                sound.set_volume(self.volume)
                sound.play()
                
                logger.debug(f"Son d'alerte joué: {sound_type}")
            else:
                logger.warning(f"Fichier son introuvable pour le type: {sound_type}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du son: {e}")
    
    def stop_all(self):
        """Arrête tous les sons et synthèses vocales en cours."""
        try:
            # Arrêter la musique pygame
            pygame.mixer.music.stop()
            
            # Vider la file d'attente des messages
            with self.queue_lock:
                self.speech_queue = []
            
            logger.info("Tous les sons et synthèses vocales arrêtés")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt des sons: {e}")
    
    def cleanup(self):
        """Nettoie les ressources utilisées par le module audio."""
        try:
            # Arrêter tous les sons
            self.stop_all()
            
            # Quitter pygame
            pygame.mixer.quit()
            pygame.quit()
            
            logger.info("Ressources audio libérées")
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des ressources audio: {e}")


def test_audio():
    """Fonction de test pour le module audio."""
    try:
        # Configuration du logging pour le test
        logging.basicConfig(level=logging.INFO)
        
        # Initialiser le module audio
        audio = AudioFeedback(language='fr')
        
        print("Test du module audio. Appuyez sur Ctrl+C pour arrêter.")
        
        # Tester la synthèse vocale
        audio.speak("Bonjour, je suis votre assistant de navigation.")
        time.sleep(3)
        
        # Tester les messages prioritaires
        audio.speak("Ceci est un message normal.")
        audio.speak("Ceci est un message prioritaire.", priority=True)
        time.sleep(5)
        
        # Tester les sons d'alerte
        print("Test des sons d'alerte...")
        audio.play_sound('info')
        time.sleep(2)
        audio.play_sound('warning')
        time.sleep(2)
        audio.play_sound('danger')
        time.sleep(2)
        
        print("Test terminé.")
            
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur")
    finally:
        if 'audio' in locals():
            audio.cleanup()
        print("Ressources audio libérées")


if __name__ == "__main__":
    test_audio() 