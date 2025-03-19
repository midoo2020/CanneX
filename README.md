# Canne - Système d'Assistance Intelligent pour Malvoyants

Un dispositif intelligent basé sur Raspberry Pi qui utilise des capteurs ultrasoniques et la vision par ordinateur pour aider les personnes malvoyantes à naviguer en toute sécurité.

## Fonctionnalités

- Détection d'obstacles par capteur ultrasonique
- Reconnaissance d'objets par caméra et intelligence artificielle
- Retour audio par synthèse vocale
- Alertes haptiques par vibration
- Interface simple et intuitive

## Matériel Nécessaire

- Raspberry Pi (3B+ ou 4 recommandé)
- Capteur ultrasonique HC-SR04
- Caméra Raspberry Pi ou webcam compatible
- Moteur de vibration
- Haut-parleur ou écouteurs
- Batterie externe (powerbank)
- Boîtier pour l'assemblage

## Installation

1. Cloner ce dépôt :
```
git clone https://github.com/username/canne.git
cd canne
```

2. Exécuter le script d'installation :
```
chmod +x setup.sh
./setup.sh
```

3. Connecter le matériel selon le schéma dans `/docs/wiring_diagram.png`

## Configuration

Éditer le fichier `config.py` pour ajuster les paramètres :
- Broches GPIO
- Seuils de distance
- Langue de la synthèse vocale
- Paramètres de la caméra

## Utilisation

Lancer l'application principale :
```
python src/main.py
```

Pour démarrer automatiquement au démarrage de Raspberry Pi :
```
sudo systemctl enable canne.service
```

## Structure du Projet

```
canne/
├── README.md               # Documentation du projet
├── requirements.txt        # Dépendances Python
├── setup.sh                # Script d'installation
├── src/                    # Code source
│   ├── main.py             # Point d'entrée principal
│   ├── config.py           # Configuration
│   ├── sensors/            # Modules des capteurs
│   │   ├── __init__.py
│   │   ├── ultrasonic.py   # Code du capteur ultrasonique
│   │   └── camera.py       # Module de caméra
│   ├── feedback/           # Modules de retour utilisateur
│   │   ├── __init__.py
│   │   ├── audio.py        # Synthèse vocale et alertes audio
│   │   └── haptic.py       # Contrôle du moteur de vibration
│   └── detection/          # Détection d'objets
│       ├── __init__.py
│       └── object_detector.py  # Détection d'objets par vision
├── models/                 # Modèles IA pré-entraînés
│   └── mobilenet_ssd/      # Modèle MobileNet SSD
├── tests/                  # Tests unitaires
└── docs/                   # Documentation
    └── wiring_diagram.png  # Schéma de câblage
```

## Dépannage

Voir les problèmes courants et leurs solutions dans la section [Wiki](https://github.com/username/canne/wiki) du projet.

## Contribution

Les contributions sont les bienvenues ! Veuillez consulter le fichier [CONTRIBUTING.md](CONTRIBUTING.md) pour les directives.

## Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails. 