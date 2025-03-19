# Tests unitaires

Ce répertoire contient les tests unitaires pour le projet Canne.

## Structure

Les tests sont organisés selon la même structure que le code source :

```
tests/
├── test_sensors/           # Tests pour les capteurs
│   ├── test_ultrasonic.py  # Tests du capteur ultrasonique
│   └── test_camera.py      # Tests de la caméra
├── test_feedback/          # Tests pour les modules de retour
│   ├── test_audio.py       # Tests du module audio
│   └── test_haptic.py      # Tests du module haptique
└── test_detection/         # Tests pour les modules de détection
    └── test_object_detector.py  # Tests de la détection d'objets
```

## Exécution des tests

Pour exécuter tous les tests :

```bash
pytest
```

Pour exécuter un groupe spécifique de tests :

```bash
pytest tests/test_sensors/
```

Pour exécuter un fichier de test spécifique :

```bash
pytest tests/test_sensors/test_ultrasonic.py
```

## Ajouter des tests

Si vous ajoutez une nouvelle fonctionnalité, veuillez ajouter également des tests unitaires correspondants. Les tests devraient couvrir :

1. Les cas d'utilisation normaux
2. Les cas limites
3. Les conditions d'erreur

Utilisez le module `unittest.mock` pour simuler les capteurs matériels et éviter la dépendance au matériel physique pendant les tests. 