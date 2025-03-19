"""
Configuration du système Canne.
Modifier ce fichier pour ajuster les paramètres du système.
"""

import os

# Répertoire du projet
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configuration des broches GPIO
GPIO_CONFIG = {
    "TRIG_PIN": 23,          # Broche trigger du capteur ultrasonique
    "ECHO_PIN": 24,          # Broche echo du capteur ultrasonique
    "VIBRATION_PIN": 18,     # Broche du moteur de vibration
}

# Configuration du capteur ultrasonique
ULTRASONIC_CONFIG = {
    "MAX_DISTANCE": 300,     # Distance maximale de détection (cm)
    "WARNING_DISTANCE": 100, # Distance d'avertissement (cm)
    "DANGER_DISTANCE": 50,   # Distance de danger (cm)
    "MEASURE_INTERVAL": 1,   # Intervalle entre les mesures (secondes)
}

# Configuration de la caméra
CAMERA_CONFIG = {
    "ENABLED": True,         # Activer/désactiver la caméra
    "RESOLUTION": (640, 480),# Résolution de la caméra
    "FRAMERATE": 24,         # Images par seconde
    "ROTATION": 0,           # Rotation de la caméra (0, 90, 180, 270)
    "CAPTURE_INTERVAL": 5,   # Intervalle entre les captures (secondes)
}

# Configuration de la détection d'objets
DETECTION_CONFIG = {
    "MODEL_DIR": os.path.join(PROJECT_ROOT, "models", "mobilenet_ssd"),
    "CONFIDENCE_THRESHOLD": 0.5,  # Seuil de confiance pour la détection
    "MAX_DETECTIONS": 5,     # Nombre maximal d'objets à annoncer
    "ENABLE_DETECTION": True,# Activer/désactiver la détection d'objets
}

# Configuration audio
AUDIO_CONFIG = {
    "ENABLED": True,         # Activer/désactiver les alertes audio
    "LANGUAGE": "fr",        # Langue de la synthèse vocale
    "VOLUME": 1.0,           # Volume (0.0 à 1.0)
    "SPEECH_RATE": 1.0,      # Vitesse de parole (0.5 à 2.0)
}

# Configuration du retour haptique
HAPTIC_CONFIG = {
    "ENABLED": True,         # Activer/désactiver le retour haptique
    "WARNING_DURATION": 0.5, # Durée de la vibration d'avertissement (secondes)
    "DANGER_DURATION": 1.0,  # Durée de la vibration de danger (secondes)
    "INFO_DURATION": 0.2,    # Durée de la vibration d'information (secondes)
    "INTENSITY": 1.0,        # Intensité de la vibration (0.0 à 1.0)
}

# Configuration de la connectivité
CONNECTIVITY_CONFIG = {
    # Configuration Bluetooth
    "BLUETOOTH": {
        "ENABLED": True,     # Activer/désactiver la connectivité Bluetooth
        "DEVICE_NAME": "Canne-Smart",  # Nom du périphérique Bluetooth
        "DISCOVERABLE": True,# Rendre le périphérique découvrable
        "PAIRING_PIN": "1234", # Code PIN pour l'appairage (si nécessaire)
        "AUTO_CONNECT": True, # Tenter automatiquement de se reconnecter
    },
    
    # Configuration USB
    "USB": {
        "ENABLED": True,     # Activer/désactiver la connectivité USB
        "BAUD_RATE": 115200, # Vitesse de communication en bauds
        "AUTO_DETECT": True, # Détecter automatiquement le port série
        "PORT": None,        # Port série spécifique (None pour auto-détection)
    },
    
    # Configuration API REST (pour la connectivité WiFi/Internet)
    "API": {
        "ENABLED": True,     # Activer/désactiver l'API REST
        "HOST": "0.0.0.0",   # Adresse d'écoute (0.0.0.0 pour toutes les interfaces)
        "PORT": 8000,        # Port d'écoute
        "AUTH_REQUIRED": True, # Authentification requise
        "USERNAME": "admin", # Nom d'utilisateur par défaut
        "PASSWORD": "canne123", # Mot de passe par défaut
        "CORS_ORIGINS": ["*"], # Origines autorisées pour les requêtes CORS
        "WEBSOCKET_ENABLED": True, # Activer les WebSockets pour les mises à jour en temps réel
    }
}

# Configuration de la journalisation
LOGGING_CONFIG = {
    "LEVEL": "INFO",         # Niveau de journalisation (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    "FILE": os.path.join(PROJECT_ROOT, "logs", "canne.log"),
    "MAX_SIZE": 10 * 1024 * 1024,  # Taille maximale du fichier journal (10 Mo)
    "BACKUP_COUNT": 5,       # Nombre de fichiers de sauvegarde à conserver
}

# Mode débogage
DEBUG = False               # Activer/désactiver le mode débogage 