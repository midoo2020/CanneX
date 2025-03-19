"""
Module pour gérer la connectivité USB de la canne.
Permet la connexion directe à un smartphone via câble USB.
"""

import os
import sys
import time
import logging
import threading
import json
import serial
import glob
from typing import Dict, Any, Optional, Callable, List

# Configuration du logger
logger = logging.getLogger(__name__)

class USBManager:
    """Classe pour gérer les connexions USB de la canne."""
    
    def __init__(self, device: str = None, baud_rate: int = 115200):
        """
        Initialise le gestionnaire USB.
        
        Args:
            device: Chemin du périphérique USB (/dev/ttyACM0, COM3, etc.)
            baud_rate: Vitesse de communication en bauds
        """
        self.device = device
        self.baud_rate = baud_rate
        self.is_running = False
        self.serial_conn = None
        self.read_thread = None
        self.data_callback = None  # Callback pour recevoir les données
        self.command_handlers = {}  # Gestionnaires de commandes
        
        # Configurer les gestionnaires de commandes par défaut
        self._setup_default_command_handlers()
        
        logger.info(f"Gestionnaire USB initialisé sur le port {device or 'auto'} à {baud_rate} bauds")
    
    def _setup_default_command_handlers(self):
        """Configure les gestionnaires de commandes par défaut."""
        self.command_handlers = {
            "get_status": self._handle_get_status,
            "start_system": self._handle_start_system,
            "stop_system": self._handle_stop_system,
            "get_distance": self._handle_get_distance,
            "get_objects": self._handle_get_objects,
        }
    
    def register_command_handler(self, command: str, handler: Callable):
        """
        Enregistre un gestionnaire pour une commande spécifique.
        
        Args:
            command: Nom de la commande
            handler: Fonction de rappel qui sera appelée lorsque la commande est reçue
        """
        self.command_handlers[command] = handler
        logger.debug(f"Gestionnaire enregistré pour la commande '{command}'")
    
    def set_data_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Définit le callback pour recevoir les données de l'application.
        
        Args:
            callback: Fonction qui sera appelée avec les données reçues
        """
        self.data_callback = callback
        logger.debug("Callback de données enregistré")
    
    @staticmethod
    def list_available_ports() -> List[str]:
        """
        Liste les ports série disponibles.
        
        Returns:
            Liste des ports série disponibles
        """
        try:
            if sys.platform.startswith('win'):
                ports = ['COM%s' % (i + 1) for i in range(256)]
            elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
                # Inclure les ports USB et ACM (Arduino)
                ports = glob.glob('/dev/tty[A-Za-z]*')
            elif sys.platform.startswith('darwin'):
                ports = glob.glob('/dev/tty.*')
            else:
                raise EnvironmentError('Système d\'exploitation non supporté')

            result = []
            for port in ports:
                try:
                    s = serial.Serial(port)
                    s.close()
                    result.append(port)
                except (OSError, serial.SerialException):
                    pass
                    
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des ports série: {e}")
            return []
    
    def _find_device(self) -> Optional[str]:
        """
        Tente de trouver automatiquement un périphérique USB connecté.
        
        Returns:
            Chemin du périphérique USB ou None si aucun n'est trouvé
        """
        ports = self.list_available_ports()
        
        if not ports:
            logger.warning("Aucun port série disponible")
            return None
        
        logger.info(f"Ports série disponibles: {', '.join(ports)}")
        return ports[0]  # Retourner le premier port disponible
    
    def start(self) -> bool:
        """
        Démarre la connexion USB.
        
        Returns:
            True si la connexion a été établie avec succès, False sinon
        """
        if self.is_running:
            logger.warning("La connexion USB est déjà en cours d'exécution")
            return True
        
        try:
            # Trouver un périphérique si non spécifié
            device = self.device
            if not device:
                device = self._find_device()
                if not device:
                    logger.error("Aucun périphérique USB trouvé")
                    return False
            
            # Ouvrir la connexion série
            self.serial_conn = serial.Serial(
                port=device,
                baudrate=self.baud_rate,
                timeout=1
            )
            
            logger.info(f"Connexion USB établie sur {device} à {self.baud_rate} bauds")
            
            # Démarrer le thread de lecture
            self.is_running = True
            self.read_thread = threading.Thread(target=self._read_loop)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'établissement de la connexion USB: {e}")
            return False
    
    def _read_loop(self):
        """Thread pour lire les données entrantes."""
        if not self.serial_conn:
            return
        
        buffer = b""
        
        while self.is_running:
            try:
                # Lire les données disponibles
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting)
                    buffer += data
                    
                    # Chercher un message JSON complet
                    if b"\n" in buffer:
                        lines = buffer.split(b"\n")
                        buffer = lines[-1]  # Garder la dernière ligne incomplète
                        
                        # Traiter les lignes complètes
                        for line in lines[:-1]:
                            if line.strip():  # Ignorer les lignes vides
                                self._process_received_data(line)
                
                # Petite pause pour éviter de surcharger le CPU
                time.sleep(0.01)
                
            except Exception as e:
                if self.is_running:  # Ignorer les erreurs lors de l'arrêt
                    logger.error(f"Erreur dans la boucle de lecture USB: {e}")
                time.sleep(1)  # Éviter une consommation excessive de CPU en cas d'erreur
    
    def _process_received_data(self, data):
        """
        Traite les données reçues.
        
        Args:
            data: Données brutes reçues
        """
        try:
            # Décoder les données JSON
            message = json.loads(data.decode('utf-8'))
            
            # Extraire la commande et les paramètres
            command = message.get("command", "")
            params = message.get("params", {})
            
            logger.debug(f"Commande USB reçue: {command}, Paramètres: {params}")
            
            # Traiter la commande
            if command in self.command_handlers:
                response = self.command_handlers[command](params)
            else:
                response = {"status": "error", "message": f"Commande '{command}' non reconnue"}
            
            # Envoyer la réponse
            self.send(response)
            
            # Appeler le callback de données si défini
            if self.data_callback:
                self.data_callback(message)
                
        except json.JSONDecodeError:
            logger.error(f"Données JSON invalides reçues: {data.decode('utf-8', errors='replace')}")
        except Exception as e:
            logger.error(f"Erreur lors du traitement des données USB: {e}")
    
    def send(self, data) -> bool:
        """
        Envoie des données via la connexion USB.
        
        Args:
            data: Données à envoyer (sera converti en JSON)
            
        Returns:
            True si les données ont été envoyées avec succès, False sinon
        """
        if not self.serial_conn or not self.is_running:
            logger.warning("Tentative d'envoi sur une connexion USB fermée")
            return False
        
        try:
            # Convertir les données en JSON et ajouter un saut de ligne
            json_data = json.dumps(data) + "\n"
            
            # Envoyer les données
            self.serial_conn.write(json_data.encode('utf-8'))
            self.serial_conn.flush()
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de données USB: {e}")
            return False
    
    def stop(self):
        """Arrête la connexion USB."""
        if not self.is_running:
            return
        
        logger.info("Arrêt de la connexion USB")
        self.is_running = False
        
        # Fermer la connexion série
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture de la connexion série: {e}")
        
        # Attendre que le thread de lecture se termine
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=5.0)
        
        self.serial_conn = None
        logger.info("Connexion USB arrêtée")
    
    # Gestionnaires de commandes par défaut
    def _handle_get_status(self, params):
        """Gère la commande pour obtenir l'état du système."""
        # Dans une implémentation réelle, cela renverrait l'état actuel du système
        return {
            "status": "success",
            "data": {
                "system_running": True,
                "battery_level": 85,
                "connected": True
            }
        }
    
    def _handle_start_system(self, params):
        """Gère la commande pour démarrer le système."""
        # Dans une implémentation réelle, cela démarrerait le système
        return {
            "status": "success",
            "message": "Système démarré"
        }
    
    def _handle_stop_system(self, params):
        """Gère la commande pour arrêter le système."""
        # Dans une implémentation réelle, cela arrêterait le système
        return {
            "status": "success",
            "message": "Système arrêté"
        }
    
    def _handle_get_distance(self, params):
        """Gère la commande pour obtenir la distance mesurée."""
        # Dans une implémentation réelle, cela renverrait la distance actuelle
        return {
            "status": "success",
            "data": {
                "distance": 120,  # Simuler une mesure de distance
                "unit": "cm",
                "timestamp": time.time()
            }
        }
    
    def _handle_get_objects(self, params):
        """Gère la commande pour obtenir les objets détectés."""
        # Dans une implémentation réelle, cela renverrait les objets détectés
        return {
            "status": "success",
            "data": {
                "objects": ["personne", "chaise"],
                "confidence": [0.95, 0.87],
                "timestamp": time.time()
            }
        }


if __name__ == "__main__":
    # Test simple de la classe USBManager
    logging.basicConfig(level=logging.INFO)
    
    # Lister les ports disponibles
    ports = USBManager.list_available_ports()
    print(f"Ports série disponibles: {ports}")
    
    if ports:
        # Démarrer le gestionnaire USB
        usb_manager = USBManager(device=ports[0])
        if usb_manager.start():
            print("Connexion USB établie avec succès")
            print("Appuyez sur Ctrl+C pour arrêter...")
            try:
                while True:
                    # Simuler l'envoi périodique de données
                    usb_manager.send({
                        "type": "status_update",
                        "timestamp": time.time(),
                        "data": {
                            "distance": 150 + int(time.time() % 100),
                            "objects_detected": ["personne", "chaise"]
                        }
                    })
                    time.sleep(5)
            except KeyboardInterrupt:
                pass
            finally:
                usb_manager.stop()
                print("Connexion USB arrêtée")
    else:
        print("Aucun port série disponible") 