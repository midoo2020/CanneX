# Modèles de reconnaissance d'objets

Ce répertoire contient les modèles pré-entraînés utilisés pour la détection et la reconnaissance d'objets.

## Fichiers nécessaires

- `frozen_inference_graph.pb` - Graphe d'inférence du modèle MobileNet SSD
- `ssd_mobilenet_v2_coco_2018_03_29.pbtxt` - Configuration du modèle
- `coco_class_labels.txt` - Liste des classes reconnues par le modèle (en français)

Ces fichiers sont automatiquement téléchargés et configurés lors de l'exécution du script `setup.sh`.

## À propos du modèle MobileNet SSD

Le modèle MobileNet SSD est un réseau de neurones conçu pour la détection d'objets en temps réel sur des appareils à ressources limitées comme le Raspberry Pi. Il offre un bon équilibre entre précision et vitesse d'exécution.

Principales caractéristiques:
- Détection de 90 classes d'objets courants
- Architecture optimisée pour les appareils mobiles
- Bonne précision pour une faible empreinte mémoire

## Utilisation alternative

Si vous souhaitez utiliser un autre modèle, vous pouvez remplacer ces fichiers, mais vous devrez également modifier le code dans `src/detection/object_detector.py` pour prendre en compte vos modifications. 