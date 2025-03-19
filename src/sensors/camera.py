"""
Module pour la gestion de la caméra.
"""

import time
import logging
import threading
import cv2
import numpy as np

# Configuration du logger
logger = logging.getLogger(__name__)

class Camera:
    """Classe pour gérer la caméra et l'acquisition d'images."""
    
    def __init__(self, resolution=(640, 480), framerate=24, rotation=0, device_id=0):
        """
        Initialise la caméra.
        
        Args:
            resolution (tuple): Résolution de la caméra (largeur, hauteur)
            framerate (int): Images par seconde
            rotation (int): Rotation de la caméra (0, 90, 180, 270)
            device_id (int): ID du périphérique de caméra (0 par défaut)
        """
        self.resolution = resolution
        self.framerate = framerate
        self.rotation = rotation
        self.device_id = device_id
        self.camera = None
        self.is_running = False
        self.capture_thread = None
        self.stop_event = threading.Event()
        self.frame_lock = threading.Lock()
        self.current_frame = None
        
        logger.info(f"Module caméra initialisé (résolution: {resolution}, fps: {framerate}, rotation: {rotation}°)")
    
    def start(self):
        """
        Démarre la caméra et l'acquisition d'images en continu.
        
        Returns:
            bool: True si le démarrage a réussi, False sinon
        """
        try:
            # Initialiser la caméra
            self.camera = cv2.VideoCapture(self.device_id)
            
            # Vérifier si la caméra est ouverte
            if not self.camera.isOpened():
                logger.error("Impossible d'ouvrir la caméra")
                return False
            
            # Configurer la résolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            
            # Configurer le framerate
            self.camera.set(cv2.CAP_PROP_FPS, self.framerate)
            
            # Réinitialiser l'événement d'arrêt
            self.stop_event.clear()
            
            # Démarrer le thread de capture
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            logger.info("Caméra démarrée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de la caméra: {e}")
            if self.camera and self.camera.isOpened():
                self.camera.release()
                self.camera = None
            return False
    
    def _capture_loop(self):
        """Fonction interne pour la capture continue des images."""
        try:
            while not self.stop_event.is_set():
                # Capturer une image
                ret, frame = self.camera.read()
                
                if not ret:
                    logger.warning("Erreur lors de la capture d'image")
                    time.sleep(0.1)
                    continue
                
                # Appliquer la rotation si nécessaire
                if self.rotation == 90:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                elif self.rotation == 180:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                elif self.rotation == 270:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                
                # Mettre à jour l'image courante
                with self.frame_lock:
                    self.current_frame = frame.copy()
                
                # Petit délai pour éviter d'utiliser trop de CPU
                time.sleep(1.0 / self.framerate)
                
        except Exception as e:
            logger.error(f"Erreur dans la boucle de capture: {e}")
        finally:
            if self.camera and self.camera.isOpened():
                self.camera.release()
                self.camera = None
            self.is_running = False
    
    def get_frame(self):
        """
        Récupère l'image la plus récente de la caméra.
        
        Returns:
            numpy.ndarray: Image au format OpenCV (BGR), ou None si aucune image n'est disponible
        """
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None
    
    def capture_single_frame(self):
        """
        Capture une seule image sans démarrer la capture continue.
        Utile pour économiser de l'énergie.
        
        Returns:
            numpy.ndarray: Image au format OpenCV (BGR), ou None si la capture a échoué
        """
        try:
            # Si la caméra est déjà en cours d'exécution, utilisez simplement get_frame()
            if self.is_running:
                return self.get_frame()
            
            # Sinon, ouvrir temporairement la caméra
            temp_camera = cv2.VideoCapture(self.device_id)
            
            if not temp_camera.isOpened():
                logger.error("Impossible d'ouvrir la caméra pour une capture unique")
                return None
            
            # Configurer la résolution
            temp_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            temp_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            
            # Capturer une image
            ret, frame = temp_camera.read()
            
            # Fermer la caméra
            temp_camera.release()
            
            if not ret:
                logger.warning("Erreur lors de la capture d'image unique")
                return None
            
            # Appliquer la rotation si nécessaire
            if self.rotation == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif self.rotation == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif self.rotation == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            logger.debug("Image unique capturée avec succès")
            return frame
            
        except Exception as e:
            logger.error(f"Erreur lors de la capture d'image unique: {e}")
            if 'temp_camera' in locals() and temp_camera.isOpened():
                temp_camera.release()
            return None
    
    def stop(self):
        """
        Arrête la caméra et libère les ressources.
        
        Returns:
            bool: True si l'arrêt a réussi, False sinon
        """
        try:
            # Signaler l'arrêt au thread de capture
            self.stop_event.set()
            
            # Attendre que le thread se termine
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=2.0)
            
            # S'assurer que la caméra est libérée
            if self.camera and self.camera.isOpened():
                self.camera.release()
                self.camera = None
            
            self.is_running = False
            logger.info("Caméra arrêtée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de la caméra: {e}")
            return False
    
    def cleanup(self):
        """Nettoie les ressources utilisées par la caméra."""
        self.stop()
        logger.info("Ressources de la caméra libérées")


def test_camera():
    """Fonction de test pour la caméra."""
    try:
        # Configuration du logging pour le test
        logging.basicConfig(level=logging.INFO)
        
        # Initialiser la caméra
        camera = Camera(resolution=(640, 480), framerate=30)
        
        print("Test de la caméra. Appuyez sur 'q' pour quitter.")
        
        # Démarrer la caméra
        if not camera.start():
            print("Impossible de démarrer la caméra")
            return
        
        # Afficher les images en continu
        try:
            while True:
                # Récupérer l'image
                frame = camera.get_frame()
                
                if frame is not None:
                    # Afficher l'image
                    cv2.imshow('Camera Test', frame)
                    
                    # Quitter si la touche 'q' est pressée
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    print("Pas d'image disponible")
                    time.sleep(0.1)
        finally:
            # Fermer la fenêtre d'affichage
            cv2.destroyAllWindows()
        
        # Tester la capture d'une seule image
        print("Test de capture d'une seule image...")
        camera.stop()
        
        frame = camera.capture_single_frame()
        if frame is not None:
            cv2.imshow('Single Frame', frame)
            print("Appuyez sur une touche pour continuer...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("Échec de la capture d'une seule image")
        
        print("Test terminé.")
            
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur")
    finally:
        if 'camera' in locals():
            camera.cleanup()
        cv2.destroyAllWindows()
        print("Ressources de la caméra libérées")


if __name__ == "__main__":
    test_camera() 