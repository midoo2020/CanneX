# Documentation

Ce répertoire contient la documentation technique du projet Canne.

## Contenu

- `wiring_diagram.png` - Schéma de câblage des composants électroniques
- Autres documents techniques sur le fonctionnement du système

## Schéma de câblage

Le fichier `wiring_diagram.png` montre comment connecter tous les composants électroniques au Raspberry Pi:

- Capteur ultrasonique HC-SR04
  - Broche TRIG: GPIO 23 (Pin 16)
  - Broche ECHO: GPIO 24 (Pin 18)
  - VCC: 5V
  - GND: GND
  
- Moteur de vibration
  - Signal: GPIO 18 (Pin 12)
  - GND: GND
  
- Autres composants (camera, audio, etc.)

## Ajouter de la documentation

Si vous ajoutez ou modifiez des fonctionnalités du système, veuillez mettre à jour la documentation correspondante dans ce répertoire. 