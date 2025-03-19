#!/usr/bin/env python3
"""
Canne - Système d'Assistance Intelligent pour Malvoyants

Programme principal qui coordonne les différents modules :
- Détection d'obstacles par capteur ultrasonique
- Reconnaissance d'objets par caméra
- Retour audio par synthèse vocale
- Alertes haptiques par vibration
- API pour les applications mobiles
- Connectivité Bluetooth et USB pour smartphones
"""

import os
import sys
import time
import signal
import logging
import logging.handlers
import threading
import RPi.GPIO as GPIO
import argparse

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modules de configuration
from src import config

# Importer les modules du projet
from src.sensors.ultrasonic import UltrasonicSensor
from src.sensors.camera import Camera
from src.detection.object_detector import ObjectDetector
from src.feedback.audio import AudioFeedback
from src.feedback.haptic import HapticFeedback

# Importation conditionnelle du module API
try:
    from src.api.server import init_api, start_api_server
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    print("Module API non disponible. Les applications mobiles ne pourront pas se connecter via WiFi.")

# Importation conditionnelle du module Bluetooth
try:
    from src.connectivity.bluetooth import BluetoothManager, is_bluetooth_available
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    print("Module Bluetooth non disponible. Les applications mobiles ne pourront pas se connecter via Bluetooth.")

# Importation conditionnelle du module USB
try:
    from src.connectivity.usb import USBManager
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False
    print("Module USB non disponible. Les applications mobiles ne pourront pas se connecter via câble USB.")

# Configurer le système de journalisation
def setup_logging():
    """Configure le système de journalisation."""
    log_level = getattr(logging, config.LOGGING_CONFIG["LEVEL"])
    log_file = config.LOGGING_CONFIG["FILE"]
    max_size = config.LOGGING_CONFIG["MAX_SIZE"]
    backup_count = config.LOGGING_CONFIG["BACKUP_COUNT"]
    
    # Créer le répertoire du fichier journal si nécessaire
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configurer le format des messages
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Créer un gestionnaire de fichier avec rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_size, backupCount=backup_count
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Créer un gestionnaire de console pour le débogage
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Configurer le logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    # Ajouter le gestionnaire de console en mode débogage
    if config.DEBUG:
        console_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
    
    return root_logger

class CanneApp:
    """Classe principale de l'application Canne."""
    
    def __init__(self):
        """Initialise l'application Canne."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialisation de l'application Canne")
        
        # Indicateur d'arrêt
        self.running = False
        self.stop_event = threading.Event()
        
        # Initialiser les modules
        self.init_modules()
        
        # Configurer les gestionnaires de signaux pour l'arrêt propre
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info("Application Canne initialisée")
    
    def init_modules(self):
        """Initialise tous les modules de l'application."""
        try:
            # Initialiser le capteur ultrasonique
            self.logger.info("Initialisation du capteur ultrasonique")
            self.ultrasonic = UltrasonicSensor(
                config.GPIO_CONFIG["TRIG_PIN"],
                config.GPIO_CONFIG["ECHO_PIN"],
                config.ULTRASONIC_CONFIG["MAX_DISTANCE"]
            )
            
            # Initialiser la caméra si elle est activée
            if config.CAMERA_CONFIG["ENABLED"]:
                self.logger.info("Initialisation de la caméra")
                self.camera = Camera(
                    resolution=config.CAMERA_CONFIG["RESOLUTION"],
                    framerate=config.CAMERA_CONFIG["FRAMERATE"],
                    rotation=config.CAMERA_CONFIG["ROTATION"]
                )
            else:
                self.camera = None
            
            # Initialiser le détecteur d'objets si la détection est activée
            if config.DETECTION_CONFIG["ENABLE_DETECTION"]:
                self.logger.info("Initialisation du détecteur d'objets")
                self.object_detector = ObjectDetector(
                    model_dir=config.DETECTION_CONFIG["MODEL_DIR"],
                    confidence_threshold=config.DETECTION_CONFIG["CONFIDENCE_THRESHOLD"],
                    max_detections=config.DETECTION_CONFIG["MAX_DETECTIONS"]
                )
            else:
                self.object_detector = None
            
            # Initialiser le module audio
            if config.AUDIO_CONFIG["ENABLED"]:
                self.logger.info("Initialisation du module audio")
                self.audio = AudioFeedback(
                    language=config.AUDIO_CONFIG["LANGUAGE"],
                    volume=config.AUDIO_CONFIG["VOLUME"],
                    speech_rate=config.AUDIO_CONFIG["SPEECH_RATE"]
                )
            else:
                self.audio = None
            
            # Initialiser le module haptique
            if config.HAPTIC_CONFIG["ENABLED"]:
                self.logger.info("Initialisation du module haptique")
                self.haptic = HapticFeedback(
                    vibration_pin=config.GPIO_CONFIG["VIBRATION_PIN"],
                    enabled=config.HAPTIC_CONFIG["ENABLED"]
                )
            else:
                self.haptic = None
            
            # Initialiser le module Bluetooth si disponible et activé
            if BLUETOOTH_AVAILABLE and config.CONNECTIVITY_CONFIG["BLUETOOTH"]["ENABLED"]:
                self.logger.info("Initialisation du module Bluetooth")
                self.bluetooth = BluetoothManager(
                    device_name=config.CONNECTIVITY_CONFIG["BLUETOOTH"]["DEVICE_NAME"]
                )
                # Configurer les gestionnaires de commandes Bluetooth
                self._setup_bluetooth_handlers()
            else:
                self.bluetooth = None
            
            # Initialiser le module USB si disponible et activé
            if USB_AVAILABLE and config.CONNECTIVITY_CONFIG["USB"]["ENABLED"]:
                self.logger.info("Initialisation du module USB")
                self.usb = USBManager(
                    device=config.CONNECTIVITY_CONFIG["USB"]["PORT"],
                    baud_rate=config.CONNECTIVITY_CONFIG["USB"]["BAUD_RATE"]
                )
                # Configurer les gestionnaires de commandes USB
                self._setup_usb_handlers()
            else:
                self.usb = None
            
            self.logger.info("Tous les modules initialisés avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation des modules: {e}")
            raise
    
    def _setup_bluetooth_handlers(self):
        """Configure les gestionnaires de commandes pour le module Bluetooth."""
        if not self.bluetooth:
            return
        
        # Enregistrer les gestionnaires de commandes personnalisés
        self.bluetooth.register_command_handler("get_status", self._handle_bt_get_status)
        self.bluetooth.register_command_handler("start_system", self._handle_bt_start_system)
        self.bluetooth.register_command_handler("stop_system", self._handle_bt_stop_system)
        self.bluetooth.register_command_handler("get_distance", self._handle_bt_get_distance)
        self.bluetooth.register_command_handler("get_objects", self._handle_bt_get_objects)
        
        # Définir le callback pour les données reçues
        self.bluetooth.set_data_callback(self._handle_bt_data)
    
    def _setup_usb_handlers(self):
        """Configure les gestionnaires de commandes pour le module USB."""
        if not self.usb:
            return
        
        # Enregistrer les gestionnaires de commandes personnalisés
        self.usb.register_command_handler("get_status", self._handle_usb_get_status)
        self.usb.register_command_handler("start_system", self._handle_usb_start_system)
        self.usb.register_command_handler("stop_system", self._handle_usb_stop_system)
        self.usb.register_command_handler("get_distance", self._handle_usb_get_distance)
        self.usb.register_command_handler("get_objects", self._handle_usb_get_objects)
        
        # Définir le callback pour les données reçues
        self.usb.set_data_callback(self._handle_usb_data)
    
    def start(self):
        """Démarre l'application."""
        if self.running:
            self.logger.warning("L'application est déjà en cours d'exécution")
            return
        
        self.logger.info("Démarrage de l'application Canne")
        self.running = True
        self.stop_event.clear()
        
        # Démarrer la caméra si elle est activée
        if self.camera:
            self.camera.start()
        
        # Démarrer le service Bluetooth si disponible
        if self.bluetooth:
            self.bluetooth.start()
        
        # Démarrer le service USB si disponible
        if self.usb:
            self.usb.start()
        
        # Message de bienvenue
        if self.audio:
            self.audio.speak("Système d'assistance pour malvoyants démarré. Je suis prêt à vous aider.")
        
        # Démarrer les threads de détection
        self.start_obstacle_detection_thread()
        self.start_object_detection_thread()
        
        self.logger.info("Application Canne démarrée")
    
    def start_obstacle_detection_thread(self):
        """Démarre le thread de détection d'obstacles."""
        self.obstacle_thread = threading.Thread(target=self.obstacle_detection_loop)
        self.obstacle_thread.daemon = True
        self.obstacle_thread.start()
        self.logger.info("Thread de détection d'obstacles démarré")
    
    def start_object_detection_thread(self):
        """Démarre le thread de détection d'objets si la caméra et le détecteur sont activés."""
        if self.camera and self.object_detector:
            self.object_thread = threading.Thread(target=self.object_detection_loop)
            self.object_thread.daemon = True
            self.object_thread.start()
            self.logger.info("Thread de détection d'objets démarré")
    
    def obstacle_detection_loop(self):
        """Boucle principale pour la détection d'obstacles."""
        self.logger.info("Démarrage de la boucle de détection d'obstacles")
        
        # Dernière distance mesurée
        last_distance = None
        
        # Dernier temps d'alerte
        last_alert_time = 0
        
        # Dernier temps de diffusion
        last_broadcast_time = 0
        
        try:
            while not self.stop_event.is_set() and self.running:
                # Mesurer la distance
                distance = self.ultrasonic.measure_distance()
                
                # Si la mesure a échoué, réessayer après un court délai
                if distance is None:
                    time.sleep(0.1)
                    continue
                
                # Déterminer si une alerte est nécessaire
                current_time = time.time()
                
                # Diffuser la distance aux clients connectés périodiquement (toutes les secondes)
                if current_time - last_broadcast_time > 1.0:
                    self._broadcast_distance(distance)
                    last_broadcast_time = current_time
                
                # N'alerter que si la distance a changé significativement
                # ou si suffisamment de temps s'est écoulé depuis la dernière alerte
                if (last_distance is None or 
                    abs(distance - last_distance) > 10 or 
                    current_time - last_alert_time > 3):
                    
                    # Alerte de danger (très proche)
                    if distance < config.ULTRASONIC_CONFIG["DANGER_DISTANCE"]:
                        self.logger.info(f"Obstacle dangereux détecté à {distance} cm")
                        
                        if self.audio:
                            self.audio.speak(f"Attention! Obstacle à {int(distance)} centimètres", priority=True)
                        
                        if self.haptic:
                            self.haptic.vibrate_danger()
                        
                        last_alert_time = current_time
                    
                    # Alerte d'avertissement (proche)
                    elif distance < config.ULTRASONIC_CONFIG["WARNING_DISTANCE"]:
                        self.logger.info(f"Obstacle proche détecté à {distance} cm")
                        
                        if self.audio:
                            self.audio.speak(f"Obstacle à {int(distance)} centimètres")
                        
                        if self.haptic:
                            self.haptic.vibrate_warning()
                        
                        last_alert_time = current_time
                
                # Mettre à jour la dernière distance mesurée
                last_distance = distance
                
                # Attendre avant la prochaine mesure
                time.sleep(config.ULTRASONIC_CONFIG["MEASURE_INTERVAL"])
                
        except Exception as e:
            self.logger.error(f"Erreur dans la boucle de détection d'obstacles: {e}")
    
    def object_detection_loop(self):
        """Boucle principale pour la détection d'objets."""
        self.logger.info("Démarrage de la boucle de détection d'objets")
        
        # Dernière détection effectuée
        last_detection_time = 0
        
        try:
            while not self.stop_event.is_set() and self.running:
                # Vérifier si c'est le moment de faire une détection
                current_time = time.time()
                if current_time - last_detection_time < config.CAMERA_CONFIG["CAPTURE_INTERVAL"]:
                    time.sleep(0.1)
                    continue
                
                # Capturer une image
                frame = self.camera.get_frame()
                
                if frame is None:
                    self.logger.warning("Pas d'image disponible pour la détection d'objets")
                    time.sleep(1)
                    continue
                
                # Détecter les objets dans l'image
                detections = self.object_detector.detect_objects(frame)
                
                # Mettre à jour le temps de la dernière détection
                last_detection_time = current_time
                
                # Si des objets sont détectés, les annoncer
                if detections:
                    summary = self.object_detector.get_detection_summary(detections)
                    self.logger.info(f"Objets détectés: {summary}")
                    
                    if self.audio:
                        self.audio.speak(summary)
                    
                    if self.haptic:
                        self.haptic.vibrate_info()
                    
                    # Diffuser les détections aux clients connectés
                    self._broadcast_objects(detections)
                
                # Attendre avant la prochaine détection
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Erreur dans la boucle de détection d'objets: {e}")
    
    def _broadcast_distance(self, distance):
        """
        Diffuse la distance mesurée aux clients connectés.
        
        Args:
            distance: Distance mesurée en centimètres
        """
        distance_data = {
            "type": "distance_update",
            "data": {
                "distance": distance,
                "unit": "cm",
                "timestamp": time.time()
            }
        }
        
        # Diffuser via Bluetooth
        if self.bluetooth and self.bluetooth.is_running:
            self.bluetooth.broadcast(distance_data)
        
        # Diffuser via USB
        if self.usb and self.usb.is_running:
            self.usb.send(distance_data)
    
    def _broadcast_objects(self, detections):
        """
        Diffuse les objets détectés aux clients connectés.
        
        Args:
            detections: Liste des détections (objet, score)
        """
        objects = [obj for obj, _ in detections]
        confidence = [score for _, score in detections]
        
        objects_data = {
            "type": "objects_update",
            "data": {
                "objects": objects,
                "confidence": confidence,
                "timestamp": time.time()
            }
        }
        
        # Diffuser via Bluetooth
        if self.bluetooth and self.bluetooth.is_running:
            self.bluetooth.broadcast(objects_data)
        
        # Diffuser via USB
        if self.usb and self.usb.is_running:
            self.usb.send(objects_data)
    
    def stop(self):
        """Arrête l'application."""
        if not self.running:
            return
        
        self.logger.info("Arrêt de l'application Canne")
        
        # Signaler l'arrêt aux threads
        self.running = False
        self.stop_event.set()
        
        # Attendre que les threads se terminent
        if hasattr(self, 'obstacle_thread') and self.obstacle_thread.is_alive():
            self.obstacle_thread.join(timeout=2.0)
        
        if hasattr(self, 'object_thread') and self.object_thread.is_alive():
            self.object_thread.join(timeout=2.0)
        
        # Arrêter le service Bluetooth
        if self.bluetooth:
            self.bluetooth.stop()
        
        # Arrêter le service USB
        if self.usb:
            self.usb.stop()
        
        # Message d'arrêt
        if self.audio:
            self.audio.speak("Arrêt du système d'assistance.")
            time.sleep(2)  # Attendre que le message soit prononcé
        
        # Nettoyer les ressources
        self.cleanup()
        
        self.logger.info("Application Canne arrêtée")
    
    def cleanup(self):
        """Nettoie toutes les ressources utilisées par l'application."""
        self.logger.info("Nettoyage des ressources")
        
        # Nettoyer les ressources de la caméra
        if hasattr(self, 'camera') and self.camera:
            self.camera.cleanup()
        
        # Nettoyer les ressources audio
        if hasattr(self, 'audio') and self.audio:
            self.audio.cleanup()
        
        # Nettoyer les ressources haptiques
        if hasattr(self, 'haptic') and self.haptic:
            self.haptic.cleanup()
        
        # Nettoyer les ressources GPIO
        GPIO.cleanup()
        
        self.logger.info("Ressources nettoyées")
    
    def signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour l'arrêt propre."""
        self.logger.info(f"Signal reçu: {signum}")
        self.stop()
        sys.exit(0)
    
    # Gestionnaires de commandes Bluetooth
    def _handle_bt_data(self, data):
        """Gère les données reçues via Bluetooth."""
        self.logger.debug(f"Données Bluetooth reçues: {data}")
        # Traiter les données selon les besoins
    
    def _handle_bt_get_status(self, params):
        """Gère la commande Bluetooth pour obtenir l'état du système."""
        return {
            "status": "success",
            "data": {
                "system_running": self.running,
                "camera_enabled": self.camera is not None,
                "detection_enabled": self.object_detector is not None,
                "last_distance": getattr(self.ultrasonic, 'last_distance', None),
                "battery_level": 85,  # Simulé pour le moment
                "timestamp": time.time()
            }
        }
    
    def _handle_bt_start_system(self, params):
        """Gère la commande Bluetooth pour démarrer le système."""
        if not self.running:
            self.start()
            return {"status": "success", "message": "Système démarré"}
        else:
            return {"status": "success", "message": "Système déjà en cours d'exécution"}
    
    def _handle_bt_stop_system(self, params):
        """Gère la commande Bluetooth pour arrêter le système."""
        if self.running:
            # Démarrer un thread pour arrêter le système (pour pouvoir répondre à la commande)
            threading.Thread(target=self.stop).start()
            return {"status": "success", "message": "Arrêt du système en cours"}
        else:
            return {"status": "success", "message": "Système déjà arrêté"}
    
    def _handle_bt_get_distance(self, params):
        """Gère la commande Bluetooth pour obtenir la distance mesurée."""
        if self.ultrasonic:
            distance = self.ultrasonic.measure_distance()
            return {
                "status": "success",
                "data": {
                    "distance": distance,
                    "unit": "cm",
                    "timestamp": time.time()
                }
            }
        else:
            return {"status": "error", "message": "Capteur ultrasonique non disponible"}
    
    def _handle_bt_get_objects(self, params):
        """Gère la commande Bluetooth pour obtenir les objets détectés."""
        if self.camera and self.object_detector:
            frame = self.camera.get_frame()
            if frame is not None:
                detections = self.object_detector.detect_objects(frame)
                objects = [obj for obj, _ in detections]
                confidence = [score for _, score in detections]
                
                return {
                    "status": "success",
                    "data": {
                        "objects": objects,
                        "confidence": confidence,
                        "timestamp": time.time()
                    }
                }
            else:
                return {"status": "error", "message": "Impossible de capturer une image"}
        else:
            return {"status": "error", "message": "Caméra ou détecteur d'objets non disponible"}
    
    # Gestionnaires de commandes USB (similaires aux gestionnaires Bluetooth)
    def _handle_usb_data(self, data):
        """Gère les données reçues via USB."""
        self.logger.debug(f"Données USB reçues: {data}")
        # Traiter les données selon les besoins
    
    def _handle_usb_get_status(self, params):
        """Gère la commande USB pour obtenir l'état du système."""
        return self._handle_bt_get_status(params)  # Réutiliser le gestionnaire Bluetooth
    
    def _handle_usb_start_system(self, params):
        """Gère la commande USB pour démarrer le système."""
        return self._handle_bt_start_system(params)  # Réutiliser le gestionnaire Bluetooth
    
    def _handle_usb_stop_system(self, params):
        """Gère la commande USB pour arrêter le système."""
        return self._handle_bt_stop_system(params)  # Réutiliser le gestionnaire Bluetooth
    
    def _handle_usb_get_distance(self, params):
        """Gère la commande USB pour obtenir la distance mesurée."""
        return self._handle_bt_get_distance(params)  # Réutiliser le gestionnaire Bluetooth
    
    def _handle_usb_get_objects(self, params):
        """Gère la commande USB pour obtenir les objets détectés."""
        return self._handle_bt_get_objects(params)  # Réutiliser le gestionnaire Bluetooth


def main():
    """Fonction principale du programme."""
    # Configurer les arguments en ligne de commande
    parser = argparse.ArgumentParser(description="Canne - Système d'Assistance Intelligent pour Malvoyants")
    parser.add_argument('--api', action='store_true', help='Activer le serveur API pour les applications mobiles')
    parser.add_argument('--api-port', type=int, default=8000, help='Port du serveur API (défaut: 8000)')
    parser.add_argument('--api-host', type=str, default='0.0.0.0', help='Hôte du serveur API (défaut: 0.0.0.0)')
    parser.add_argument('--bluetooth', action='store_true', help='Activer la connectivité Bluetooth')
    parser.add_argument('--usb', action='store_true', help='Activer la connectivité USB')
    parser.add_argument('--no-hardware', action='store_true', help='Mode sans matériel (simulation)')
    
    args = parser.parse_args()
    
    # Si le mode sans matériel est activé, configurer les mocks
    if args.no_hardware:
        print("Mode sans matériel activé: le hardware sera simulé")
        # TODO: Configurer les mocks pour les capteurs
    
    # Configurer le système de journalisation
    logger = setup_logging()
    
    # Threads pour les services de connectivité
    api_thread = None
    
    try:
        # Créer et démarrer l'application
        app = CanneApp()
        app.start()
        
        # Initialiser et démarrer le serveur API si activé
        if args.api or config.CONNECTIVITY_CONFIG["API"]["ENABLED"]:
            if API_AVAILABLE:
                logger.info(f"Démarrage du serveur API sur {args.api_host}:{args.api_port}")
                
                # Initialiser l'API avec l'instance de l'application
                init_api(app)
                
                # Démarrer le serveur API dans un thread séparé
                api_thread = threading.Thread(
                    target=start_api_server,
                    args=(args.api_host, args.api_port)
                )
                api_thread.daemon = True
                api_thread.start()
                
                logger.info("Serveur API démarré")
            else:
                logger.error("Serveur API demandé mais le module API n'est pas disponible")
                print("Erreur: Serveur API demandé mais le module API n'est pas disponible")
                print("Installez les dépendances nécessaires: pip install fastapi uvicorn")
        
        # Boucle principale du programme
        logger.info("Démarrage de la boucle principale")
        while app.running:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Erreur dans la fonction principale: {e}")
    finally:
        # S'assurer que l'application est arrêtée proprement
        if 'app' in locals():
            app.stop()


if __name__ == "__main__":
    main() 