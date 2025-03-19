#!/bin/bash

echo "Installation du système Canne pour Assistance aux Malvoyants"
echo "==========================================================="

# Vérifier si le script est exécuté en tant que root
if [ "$EUID" -ne 0 ]; then
  echo "Veuillez exécuter ce script en tant que root (avec sudo)"
  exit 1
fi

# Mise à jour du système
echo "Mise à jour du système..."
apt update
apt upgrade -y

# Installation des dépendances système
echo "Installation des dépendances système..."
apt install -y python3-pip python3-dev libatlas-base-dev libopenjp2-7 libtiff5 portaudio19-dev

# Installation des dépendances Python
echo "Installation des dépendances Python..."
pip3 install -r requirements.txt

# Créer les répertoires nécessaires
echo "Création des répertoires de projet..."
mkdir -p models/mobilenet_ssd
mkdir -p docs

# Télécharger les modèles pré-entraînés
echo "Téléchargement des modèles pré-entraînés..."
wget -O models/mobilenet_ssd/frozen_inference_graph.pb https://github.com/opencv/opencv_extra/raw/master/testdata/dnn/ssd_mobilenet_v2_coco_2018_03_29.pb
wget -O models/mobilenet_ssd/ssd_mobilenet_v2_coco_2018_03_29.pbtxt https://github.com/opencv/opencv/raw/master/samples/dnn/face_detector/opencv_face_detector.pbtxt

# Créer un fichier de labels pour COCO
echo "Création des labels COCO..."
cat > models/mobilenet_ssd/coco_class_labels.txt << EOL
personne
vélo
voiture
moto
avion
bus
train
camion
bateau
feu tricolore
borne fontaine
panneau stop
parcmètre
banc
oiseau
chat
chien
cheval
mouton
vache
éléphant
ours
zèbre
girafe
sac à dos
parapluie
sac à main
cravate
valise
frisbee
skis
snowboard
ballon de sport
cerf-volant
batte de baseball
gant de baseball
skateboard
planche de surf
raquette de tennis
bouteille
verre à vin
tasse
fourchette
couteau
cuillère
bol
banane
pomme
sandwich
orange
brocoli
carotte
hot-dog
pizza
donut
gâteau
chaise
canapé
plante en pot
lit
table
toilette
télévision
ordinateur portable
souris
télécommande
clavier
téléphone portable
four à micro-ondes
four
grille-pain
évier
réfrigérateur
livre
horloge
vase
ciseaux
ours en peluche
sèche-cheveux
brosse à dents
EOL

# Configuration du service systemd
echo "Configuration du service systemd..."
cat > /etc/systemd/system/canne.service << EOL
[Unit]
Description=Canne - Système d'Assistance pour Malvoyants
After=network.target

[Service]
ExecStart=/usr/bin/python3 $(pwd)/src/main.py
WorkingDirectory=$(pwd)
Restart=always
User=$SUDO_USER

[Install]
WantedBy=multi-user.target
EOL

# Vérifier que RPi.GPIO peut accéder aux broches GPIO
echo "Configuration des permissions GPIO..."
usermod -a -G gpio $SUDO_USER

echo ""
echo "Installation terminée avec succès !"
echo "Exécutez 'python3 src/main.py' pour démarrer l'application"
echo "Ou activez le service avec 'sudo systemctl enable canne.service'"
echo "" 