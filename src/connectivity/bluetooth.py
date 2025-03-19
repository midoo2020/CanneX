"""
Module pour gérer la connectivité Bluetooth de la canne.
Permet l'appairage et la communication avec les smartphones.
"""

import os
import sys
import time
import logging
import threading
import json
from typing import Dict, Any, Optional, Callable

# Vérifier si nous sommes sur un Raspberry Pi pour pouvoir importer les bibliothèques Bluetooth
try:
    import bluetooth
    from bluetooth.ble import DiscoveryService, GATTRequester
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    print("Avertissement: Bibliothèques Bluetooth non disponibles. "
          "Exécutez 'pip install pybluez pybluez2' pour les installer.")

# Configuration du logger
logger = logging.getLogger(__name__)

class BluetoothManager:
    """Classe pour gérer les connexions Bluetooth de la canne."""
    
    def __init__(self, device_name: str = "Canne-Smart"):
        """
        Initialise le gestionnaire Bluetooth.
        
        Args:
            device_name: Nom du périphérique Bluetooth
        """
        self.device_name = device_name
        self.is_running = False
        self.clients = {}  # Dictionnaire des clients connectés
        self.server_socket = None
        self.discovery_thread = None
        self.server_thread = None
        self.data_callback = None  # Callback pour recevoir les données
        self.command_handlers = {}  # Gestionnaires de commandes
        
        # Vérifier si le Bluetooth est disponible
        if not BLUETOOTH_AVAILABLE:
            logger.error("Les bibliothèques Bluetooth ne sont pas disponibles")
            return
        
        # Configurer les gestionnaires de commandes par défaut
        self._setup_default_command_handlers()
        
        logger.info(f"Gestionnaire Bluetooth initialisé avec le nom '{device_name}'")
    
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
    
    def start(self):
        """Démarre le service Bluetooth."""
        if not BLUETOOTH_AVAILABLE:
            logger.error("Impossible de démarrer le service Bluetooth: bibliothèques non disponibles")
            return False
        
        if self.is_running:
            logger.warning("Le service Bluetooth est déjà en cours d'exécution")
            return True
        
        try:
            # Configurer le socket serveur Bluetooth
            self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_socket.bind(("", bluetooth.PORT_ANY))
            self.server_socket.listen(1)
            
            port = self.server_socket.getsockname()[1]
            
            # Rendre le service détectable
            bluetooth.advertise_service(
                self.server_socket, self.device_name,
                service_id="00001101-0000-1000-8000-00805F9B34FB",
                service_classes=["00001101-0000-1000-8000-00805F9B34FB"],
                profiles=[bluetooth.SERIAL_PORT_PROFILE]
            )
            
            logger.info(f"Service Bluetooth démarré, attente de connexions sur le port {port}")
            
            # Démarrer le thread d'écoute des connexions
            self.is_running = True
            self.server_thread = threading.Thread(target=self._connection_handler)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du service Bluetooth: {e}")
            return False
    
    def _connection_handler(self):
        """Thread pour gérer les connexions entrantes."""
        while self.is_running:
            try:
                # Attendre une connexion client
                client_sock, client_info = self.server_socket.accept()
                client_id = f"{client_info[0]}:{client_info[1]}"
                
                logger.info(f"Connexion Bluetooth acceptée de {client_info[0]}")
                
                # Ajouter le client à la liste des clients
                self.clients[client_id] = {
                    "socket": client_sock,
                    "info": client_info,
                    "thread": None
                }
                
                # Démarrer un thread pour gérer cette connexion
                client_thread = threading.Thread(
                    target=self._client_handler,
                    args=(client_id,)
                )
                client_thread.daemon = True
                client_thread.start()
                
                self.clients[client_id]["thread"] = client_thread
                
            except Exception as e:
                if self.is_running:  # Ignorer les erreurs lors de l'arrêt
                    logger.error(f"Erreur dans le gestionnaire de connexions: {e}")
                time.sleep(1)  # Éviter une consommation excessive de CPU en cas d'erreur
    
    def _client_handler(self, client_id):
        """
        Gère la communication avec un client spécifique.
        
        Args:
            client_id: Identifiant unique du client
        """
        client_sock = self.clients[client_id]["socket"]
        
        try:
            client_sock.settimeout(60.0)  # 60 secondes de timeout
            
            while self.is_running:
                # Recevoir des données du client
                data = client_sock.recv(1024)
                
                if not data:
                    logger.info(f"Client Bluetooth {client_id} déconnecté")
                    break
                
                # Traiter les données reçues
                self._process_received_data(client_id, data)
                
        except Exception as e:
            logger.error(f"Erreur dans la communication avec le client {client_id}: {e}")
        finally:
            # Nettoyer la connexion
            try:
                client_sock.close()
            except:
                pass
            
            # Supprimer le client de la liste
            if client_id in self.clients:
                del self.clients[client_id]
                
            logger.info(f"Client Bluetooth {client_id} déconnecté et nettoyé")
    
    def _process_received_data(self, client_id, data):
        """
        Traite les données reçues d'un client.
        
        Args:
            client_id: Identifiant du client
            data: Données brutes reçues
        """
        try:
            # Décoder les données JSON
            message = json.loads(data.decode('utf-8'))
            
            # Extraire la commande et les paramètres
            command = message.get("command", "")
            params = message.get("params", {})
            
            logger.debug(f"Commande Bluetooth reçue: {command}, Paramètres: {params}")
            
            # Traiter la commande
            if command in self.command_handlers:
                response = self.command_handlers[command](params)
            else:
                response = {"status": "error", "message": f"Commande '{command}' non reconnue"}
            
            # Envoyer la réponse au client
            self.send_to_client(client_id, response)
            
            # Appeler le callback de données si défini
            if self.data_callback:
                self.data_callback(message)
                
        except json.JSONDecodeError:
            logger.error(f"Données JSON invalides reçues du client {client_id}")
            response = {"status": "error", "message": "Format de données invalide"}
            self.send_to_client(client_id, response)
        except Exception as e:
            logger.error(f"Erreur lors du traitement des données du client {client_id}: {e}")
    
    def send_to_client(self, client_id, data):
        """
        Envoie des données à un client spécifique.
        
        Args:
            client_id: Identifiant du client
            data: Données à envoyer (sera converti en JSON)
        """
        if client_id not in self.clients:
            logger.warning(f"Tentative d'envoi à un client inexistant: {client_id}")
            return False
        
        try:
            client_sock = self.clients[client_id]["socket"]
            json_data = json.dumps(data)
            client_sock.send(json_data.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de données au client {client_id}: {e}")
            return False
    
    def broadcast(self, data):
        """
        Diffuse des données à tous les clients connectés.
        
        Args:
            data: Données à envoyer (sera converti en JSON)
        """
        if not self.clients:
            return
        
        json_data = json.dumps(data)
        encoded_data = json_data.encode('utf-8')
        
        disconnected_clients = []
        
        for client_id, client_info in self.clients.items():
            try:
                client_info["socket"].send(encoded_data)
            except Exception as e:
                logger.error(f"Erreur lors de la diffusion au client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Nettoyer les clients déconnectés
        for client_id in disconnected_clients:
            if client_id in self.clients:
                try:
                    self.clients[client_id]["socket"].close()
                except:
                    pass
                del self.clients[client_id]
    
    def stop(self):
        """Arrête le service Bluetooth."""
        if not self.is_running:
            return
        
        logger.info("Arrêt du service Bluetooth")
        self.is_running = False
        
        # Fermer toutes les connexions client
        for client_id, client_info in list(self.clients.items()):
            try:
                client_info["socket"].close()
            except:
                pass
        
        # Fermer le socket serveur
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Attendre que les threads se terminent
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5.0)
        
        self.clients = {}
        logger.info("Service Bluetooth arrêté")
    
    # Gestionnaires de commandes par défaut
    def _handle_get_status(self, params):
        """Gère la commande pour obtenir l'état du système."""
        # Dans une implémentation réelle, cela renverrait l'état actuel du système
        return {
            "status": "success",
            "data": {
                "system_running": True,
                "battery_level": 85,
                "connected_clients": len(self.clients)
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


# Classe pour scanner les appareils Bluetooth environnants
class BluetoothScanner:
    """Classe pour scanner les appareils Bluetooth environnants."""
    
    @staticmethod
    def scan_devices(duration=8):
        """
        Scan les appareils Bluetooth à proximité.
        
        Args:
            duration: Durée du scan en secondes
            
        Returns:
            Liste des appareils trouvés (adresse, nom)
        """
        if not BLUETOOTH_AVAILABLE:
            logger.error("Impossible de scanner: bibliothèques Bluetooth non disponibles")
            return []
        
        try:
            logger.info(f"Début du scan Bluetooth ({duration} secondes)...")
            devices = bluetooth.discover_devices(
                duration=duration,
                lookup_names=True,
                flush_cache=True
            )
            
            logger.info(f"Scan terminé, {len(devices)} appareils trouvés")
            return devices
        except Exception as e:
            logger.error(f"Erreur lors du scan Bluetooth: {e}")
            return []
    
    @staticmethod
    def scan_ble_services(duration=5):
        """
        Scan les services Bluetooth Low Energy à proximité.
        
        Args:
            duration: Durée du scan en secondes
            
        Returns:
            Dictionnaire des services trouvés
        """
        if not BLUETOOTH_AVAILABLE:
            logger.error("Impossible de scanner: bibliothèques Bluetooth non disponibles")
            return {}
        
        try:
            logger.info(f"Début du scan BLE ({duration} secondes)...")
            service = DiscoveryService()
            devices = service.discover(duration)
            
            logger.info(f"Scan BLE terminé, {len(devices)} appareils trouvés")
            return devices
        except Exception as e:
            logger.error(f"Erreur lors du scan BLE: {e}")
            return {}


# Fonction pour vérifier la disponibilité du Bluetooth sur le système
def is_bluetooth_available():
    """
    Vérifie si le Bluetooth est disponible sur le système.
    
    Returns:
        True si le Bluetooth est disponible, False sinon
    """
    if not BLUETOOTH_AVAILABLE:
        return False
    
    try:
        # Tenter de créer un socket Bluetooth
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.close()
        return True
    except Exception as e:
        logger.error(f"Bluetooth n'est pas disponible sur ce système: {e}")
        return False


if __name__ == "__main__":
    # Test simple de la classe BluetoothManager
    logging.basicConfig(level=logging.INFO)
    
    print("Vérification de la disponibilité Bluetooth...")
    if is_bluetooth_available():
        print("Bluetooth est disponible!")
        
        # Scanner les appareils
        print("Recherche d'appareils Bluetooth à proximité...")
        devices = BluetoothScanner.scan_devices()
        
        if devices:
            print("Appareils trouvés:")
            for addr, name in devices:
                print(f"  {addr} - {name}")
        else:
            print("Aucun appareil trouvé")
        
        # Démarrer le service Bluetooth
        print("Démarrage du service Bluetooth...")
        bt_manager = BluetoothManager()
        if bt_manager.start():
            print("Service Bluetooth démarré avec succès")
            print("Appuyez sur Ctrl+C pour arrêter...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                bt_manager.stop()
                print("Service Bluetooth arrêté")
    else:
        print("Bluetooth n'est pas disponible sur ce système") 