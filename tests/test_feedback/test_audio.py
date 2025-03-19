"""
Tests unitaires pour le module de retour audio.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
import pygame
from src.feedback.audio import AudioFeedback

class TestAudioFeedback(unittest.TestCase):
    """Tests pour la classe AudioFeedback."""
    
    @patch('pygame.mixer.init')
    @patch('pygame.init')
    def setUp(self, mock_pygame_init, mock_mixer_init):
        """Configuration avant chaque test."""
        self.language = 'fr'
        self.volume = 0.8
        self.speech_rate = 1.0
        
        # Créer une instance du module audio
        self.audio = AudioFeedback(
            language=self.language,
            volume=self.volume,
            speech_rate=self.speech_rate
        )
    
    @patch('pygame.mixer.quit')
    @patch('pygame.quit')
    def tearDown(self, mock_pygame_quit, mock_mixer_quit):
        """Nettoyage après chaque test."""
        if hasattr(self, 'audio'):
            self.audio.cleanup()
    
    @patch('gtts.gTTS')
    @patch('pygame.mixer.music.load')
    @patch('pygame.mixer.music.play')
    @patch('pygame.mixer.music.get_busy')
    @patch('pygame.mixer.music.set_volume')
    @patch('os.remove')
    def test_speak(self, mock_remove, mock_set_volume, mock_get_busy, 
                   mock_play, mock_load, mock_gTTS):
        """Teste la synthèse vocale."""
        # Configurer les mocks
        mock_tts_instance = MagicMock()
        mock_gTTS.return_value = mock_tts_instance
        
        # Simuler que l'audio se termine immédiatement
        mock_get_busy.side_effect = [True, False]
        
        # Appeler la méthode à tester
        test_text = "Ceci est un test"
        self.audio.speak(test_text)
        
        # Forcer l'exécution du thread (dans les tests, on exécute directement)
        # Note: ceci est une simplification, en pratique il faudrait synchroniser le thread
        self.audio._speak_worker()
        
        # Vérifier que gTTS a été appelé avec les bons paramètres
        mock_gTTS.assert_called_once_with(
            text=test_text, 
            lang=self.language, 
            slow=(self.speech_rate < 1.0)
        )
        
        # Vérifier que la méthode save de gTTS a été appelée
        mock_tts_instance.save.assert_called_once()
        
        # Vérifier que le volume a été défini
        mock_set_volume.assert_called_once_with(self.volume)
        
        # Vérifier que le fichier audio a été chargé et joué
        mock_load.assert_called_once()
        mock_play.assert_called_once()
        
        # Vérifier que le fichier temporaire a été supprimé
        mock_remove.assert_called_once()
    
    @patch('pygame.mixer.music.stop')
    def test_stop_all(self, mock_stop):
        """Teste l'arrêt de tous les sons."""
        # Ajouter quelques messages à la file d'attente
        self.audio.speak("Message 1")
        self.audio.speak("Message 2")
        
        # Appeler la méthode à tester
        self.audio.stop_all()
        
        # Vérifier que stop a été appelé
        mock_stop.assert_called_once()
        
        # Vérifier que la file d'attente est vide
        self.assertEqual(len(self.audio.speech_queue), 0)
    
    @patch('pygame.mixer.Sound')
    @patch('os.path.exists')
    def test_play_sound(self, mock_exists, mock_Sound):
        """Teste la lecture d'un fichier son."""
        # Configurer les mocks
        mock_exists.return_value = True
        mock_sound_instance = MagicMock()
        mock_Sound.return_value = mock_sound_instance
        
        # Appeler la méthode à tester
        self.audio.play_sound('warning')
        
        # Vérifier que Sound a été appelé
        mock_Sound.assert_called_once()
        
        # Vérifier que le volume a été défini
        mock_sound_instance.set_volume.assert_called_once_with(self.volume)
        
        # Vérifier que le son a été joué
        mock_sound_instance.play.assert_called_once()
    
    def test_priority_message(self):
        """Teste la priorité des messages."""
        # Ajouter un message normal et un message prioritaire
        self.audio.speak("Message normal")
        self.audio.speak("Message prioritaire", priority=True)
        
        # Vérifier que le message prioritaire est en tête de file
        self.assertEqual(self.audio.speech_queue[0], "Message prioritaire")

if __name__ == '__main__':
    unittest.main() 