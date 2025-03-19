#!/usr/bin/env python3
"""
Script pour générer un schéma de câblage pour le projet Canne.
Utilise Matplotlib pour créer une visualisation des connexions entre 
le Raspberry Pi et les différents composants électroniques.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np

# Définir les couleurs pour les différents composants
COLORS = {
    'raspberry_pi': '#67b93e',    # Vert
    'ultrasonic': '#3d85c6',      # Bleu
    'vibration': '#e69138',       # Orange
    'camera': '#cc0000',          # Rouge
    'bluetooth': '#0066cc',       # Bleu foncé
    'wifi': '#6aa84f',            # Vert foncé
    'usb': '#674ea7',             # Violet
    'phone': '#f44336',           # Rouge vif
    'background': '#f5f5f5',      # Gris très clair
}

def draw_wire(ax, start_pos, end_pos, color, lw=2, zorder=1, style='-', curve_height=0.5, annotate=None):
    """Dessine un fil entre deux points avec une courbe.
    
    Args:
        ax: Axe matplotlib
        start_pos: (x, y) du point de départ
        end_pos: (x, y) du point d'arrivée
        color: Couleur du fil
        lw: Épaisseur du trait
        zorder: Ordre Z pour l'affichage des couches
        style: Style de ligne ('-', '--', '-.', ':')
        curve_height: Hauteur de la courbe
        annotate: Texte d'annotation à ajouter au fil
    """
    # Point de contrôle pour la courbe
    control_x = (start_pos[0] + end_pos[0]) / 2
    control_y = (start_pos[1] + end_pos[1]) / 2 + curve_height
    
    # Définir le chemin de la courbe
    verts = [
        start_pos,
        (control_x, control_y),
        end_pos,
    ]
    codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
    path = Path(verts, codes)
    
    # Dessiner la courbe
    patch = patches.PathPatch(path, facecolor='none', edgecolor=color, lw=lw, zorder=zorder, linestyle=style)
    ax.add_patch(patch)
    
    # Ajouter une annotation si spécifiée
    if annotate:
        # Position de l'annotation au milieu de la courbe
        ax.annotate(
            annotate, 
            xy=(control_x, control_y),
            xytext=(control_x, control_y + 0.15),
            fontsize=7,
            ha='center',
            va='bottom',
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8)
        )

def draw_smartphone(ax, pos, width=2, height=3.5, label="Smartphone"):
    """Dessine un smartphone.
    
    Args:
        ax: Axe matplotlib
        pos: (x, y) de la position du coin inférieur gauche
        width: Largeur du smartphone
        height: Hauteur du smartphone
        label: Étiquette à afficher
    """
    # Corps du téléphone
    body = patches.Rectangle(
        pos, width, height, 
        facecolor=COLORS['phone'], 
        edgecolor='black', 
        lw=1.5, 
        zorder=2,
        alpha=0.8
    )
    ax.add_patch(body)
    
    # Écran
    screen_margin = 0.15
    screen = patches.Rectangle(
        (pos[0] + screen_margin, pos[1] + screen_margin), 
        width - 2*screen_margin, 
        height - 2*screen_margin, 
        facecolor='white', 
        edgecolor='black', 
        lw=0.5, 
        zorder=3,
        alpha=0.9
    )
    ax.add_patch(screen)
    
    # Bouton central
    button_y = pos[1] + 0.3
    button = patches.Circle(
        (pos[0] + width/2, button_y), 
        0.15, 
        facecolor='lightgray', 
        edgecolor='black', 
        lw=0.5, 
        zorder=3
    )
    ax.add_patch(button)
    
    # Afficher l'interface de l'application (simplifié)
    app_y = pos[1] + height - 1.5
    
    # Titre de l'application
    ax.text(
        pos[0] + width/2, app_y + 0.8,
        "App Canne", 
        fontsize=8, 
        fontweight='bold',
        ha='center', 
        zorder=4
    )
    
    # Un bouton dans l'application
    app_button1 = patches.Rectangle(
        (pos[0] + 0.3, app_y), 
        width - 0.6, 
        0.4, 
        facecolor='lightblue', 
        edgecolor='blue', 
        lw=0.5, 
        zorder=3,
        alpha=0.8
    )
    ax.add_patch(app_button1)
    
    # Texte du bouton
    ax.text(
        pos[0] + width/2, app_y + 0.2,
        "Connecter", 
        fontsize=7, 
        ha='center', 
        zorder=4
    )
    
    # Étiquette du smartphone
    ax.text(
        pos[0] + width/2, pos[1] + height + 0.2,
        label, 
        fontsize=10, 
        fontweight='bold',
        ha='center'
    )
    
    return (pos[0] + width/2, pos[1] + height)  # Point de connexion en haut

def draw_connection_icon(ax, pos, icon_type, size=0.4, label=None):
    """Dessine une icône de connexion.
    
    Args:
        ax: Axe matplotlib
        pos: (x, y) de la position centrale
        icon_type: Type d'icône ('bluetooth', 'wifi', 'usb')
        size: Taille de l'icône
        label: Étiquette à afficher
    """
    if icon_type == 'bluetooth':
        # Icône Bluetooth (simplifié)
        color = COLORS['bluetooth']
        bluetooth_symbol = patches.Circle(
            pos, size/2,
            facecolor=color, 
            edgecolor='black', 
            lw=0.5, 
            zorder=3,
            alpha=0.8
        )
        ax.add_patch(bluetooth_symbol)
        
        # Dessin du "B" stylisé à l'intérieur
        bt_points = np.array([
            [pos[0]-size/4, pos[1]],
            [pos[0]+size/4, pos[1]+size/2],
            [pos[0]+size/4, pos[1]-size/2],
            [pos[0]-size/4, pos[1]]
        ])
        ax.plot(bt_points[:, 0], bt_points[:, 1], 'white', lw=1.5, zorder=4)
        
    elif icon_type == 'wifi':
        # Icône WiFi (arcs concentriques)
        color = COLORS['wifi']
        circle = patches.Circle(
            pos, size,
            facecolor=color, 
            edgecolor='black', 
            lw=0.5, 
            zorder=3,
            alpha=0.8
        )
        ax.add_patch(circle)
        
        # Les arcs WiFi
        for i in range(3):
            arc_size = (i+1) * size/4
            start_angle = 210  # en degrés
            end_angle = 330    # en degrés
            arc = patches.Arc(
                pos, 
                arc_size*2, 
                arc_size*2, 
                theta1=start_angle, 
                theta2=end_angle,
                lw=1.5, 
                color='white', 
                zorder=4
            )
            ax.add_patch(arc)
            
        # Point au centre
        dot = patches.Circle(
            pos, size/10,
            facecolor='white', 
            edgecolor='white', 
            lw=0.5, 
            zorder=4
        )
        ax.add_patch(dot)
        
    elif icon_type == 'usb':
        # Icône USB (symbole de trident)
        color = COLORS['usb']
        usb_symbol = patches.Rectangle(
            (pos[0]-size/2, pos[1]-size/2), 
            size, 
            size, 
            facecolor=color, 
            edgecolor='black', 
            lw=0.5, 
            zorder=3,
            alpha=0.8
        )
        ax.add_patch(usb_symbol)
        
        # Le trident USB
        usb_center_x = pos[0]
        usb_base_y = pos[1] - size/3
        
        # Ligne verticale centrale
        ax.plot(
            [usb_center_x, usb_center_x], 
            [usb_base_y, pos[1]+size/3], 
            'white', 
            lw=1.5, 
            zorder=4
        )
        
        # Les trois branches
        for offset in [-0.15, 0, 0.15]:
            ax.plot(
                [usb_center_x + offset, usb_center_x + offset], 
                [pos[1] + size/3 - 0.05, pos[1] + size/3], 
                'white', 
                lw=1.5, 
                zorder=4
            )
        
        # Ligne horizontale du bas
        ax.plot(
            [usb_center_x - size/3, usb_center_x + size/3], 
            [usb_base_y, usb_base_y], 
            'white', 
            lw=1.5, 
            zorder=4
        )
    
    # Ajouter une étiquette si spécifiée
    if label:
        ax.text(
            pos[0], pos[1] - size - 0.1,
            label, 
            fontsize=8, 
            ha='center',
            va='top'
        )

def create_wiring_diagram():
    """Crée un schéma de câblage pour le projet Canne."""
    # Créer la figure et l'axe
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Ajouter un fond légèrement coloré
    ax.add_patch(patches.Rectangle((0, 0), 15, 10, facecolor=COLORS['background'], alpha=0.3))
    
    # Paramètres pour le placement des composants
    pi_width, pi_height = 4, 2.5
    ultrasonic_width, ultrasonic_height = 2, 1
    vibration_width, vibration_height = 1, 1
    camera_width, camera_height = 1.5, 1
    
    # Positions des composants
    pi_pos = (5, 4)  # Position centrale
    ultrasonic_pos = (10, 7)
    vibration_pos = (10, 4.5)
    camera_pos = (10, 2)
    smartphone_pos = (12, 1)
    
    # Points de connexion pour les smartphones
    bt_connection_point = (pi_pos[0] + 3, pi_pos[1] + 2.2)
    wifi_connection_point = (pi_pos[0] + 1.5, pi_pos[1] + 2.2)
    usb_connection_point = (pi_pos[0] - 1, pi_pos[1] + 0.5)
    
    # Dessiner le Raspberry Pi (plus de détails)
    # Corps du Raspberry Pi
    ax.add_patch(patches.Rectangle(pi_pos, pi_width, pi_height, 
                                  facecolor=COLORS['raspberry_pi'], 
                                  edgecolor='black', lw=2, zorder=2))
    
    # Connecteurs USB
    usb_width, usb_height = 0.3, 0.2
    usb_pos_x = pi_pos[0] + 0.3
    for i in range(4):
        usb_pos_y = pi_pos[1] + pi_height - 0.4 - i * 0.3
        if i < 2:
            # USB classiques
            ax.add_patch(patches.Rectangle((usb_pos_x, usb_pos_y), usb_width, usb_height, 
                                          facecolor='silver', edgecolor='gray', lw=0.5, zorder=3))
        else:
            # USB plus petits (microUSB)
            ax.add_patch(patches.Rectangle((usb_pos_x + 0.1, usb_pos_y), usb_width - 0.1, usb_height - 0.05, 
                                          facecolor='silver', edgecolor='gray', lw=0.5, zorder=3))
    
    # Port Ethernet
    ethernet_width, ethernet_height = 0.5, 0.3
    ethernet_pos = (pi_pos[0] + pi_width - ethernet_width - 0.2, pi_pos[1] + pi_height - 0.4)
    ax.add_patch(patches.Rectangle(ethernet_pos, ethernet_width, ethernet_height, 
                                  facecolor='silver', edgecolor='gray', lw=0.5, zorder=3))
    
    # Connecteur HDMI
    hdmi_width, hdmi_height = 0.4, 0.2
    hdmi_pos = (pi_pos[0] + pi_width - hdmi_width - 0.8, pi_pos[1] + pi_height - 0.4)
    ax.add_patch(patches.Rectangle(hdmi_pos, hdmi_width, hdmi_height, 
                                  facecolor='black', edgecolor='gray', lw=0.5, zorder=3))
    
    # Connecteur caméra (CSI)
    csi_width, csi_height = 0.4, 0.1
    csi_pos = (pi_pos[0] + pi_width/2 - csi_width/2, pi_pos[1] + pi_height - 0.7)
    ax.add_patch(patches.Rectangle(csi_pos, csi_width, csi_height, 
                                  facecolor='gray', edgecolor='black', lw=0.5, zorder=3))
    ax.text(csi_pos[0] + csi_width/2, csi_pos[1] - 0.1, 'CSI', fontsize=6, ha='center')
    
    # Module WiFi/Bluetooth intégré (représentation visuelle)
    wifi_bt_module_pos = (pi_pos[0] + pi_width - 1, pi_pos[1] + 0.3)
    wifi_bt_module_width, wifi_bt_module_height = 0.8, 0.5
    ax.add_patch(patches.Rectangle(wifi_bt_module_pos, wifi_bt_module_width, wifi_bt_module_height, 
                                  facecolor='#90caf9', edgecolor='black', lw=0.5, zorder=3, alpha=0.7))
    ax.text(wifi_bt_module_pos[0] + wifi_bt_module_width/2, wifi_bt_module_pos[1] + wifi_bt_module_height/2, 
           'WiFi/BT', fontsize=6, ha='center', va='center')
    
    # Rangée de GPIO pins
    gpio_start_x = pi_pos[0] + 0.5
    gpio_start_y = pi_pos[1] + 0.1
    gpio_width, gpio_height = 0.1, 0.1
    gpio_spacing = 0.15
    
    for i in range(20):
        pin_x = gpio_start_x + i * gpio_spacing
        if pin_x < pi_pos[0] + pi_width - 0.5:  # Éviter de déborder du Pi
            ax.add_patch(patches.Rectangle((pin_x, gpio_start_y), gpio_width, gpio_height, 
                                          facecolor='gold', edgecolor='black', lw=0.5, zorder=3))
    
    # Étiquette pour le Raspberry Pi
    ax.text(pi_pos[0] + pi_width/2, pi_pos[1] + pi_height/2, 'Raspberry Pi 4',
            ha='center', va='center', fontsize=14, fontweight='bold', color='white')
    
    # Broches GPIO spécifiques pour nos composants
    gpio_pins = {
        'GPIO17 (Trig)': (pi_pos[0] + pi_width, pi_pos[1] + 2.2),
        'GPIO27 (Echo)': (pi_pos[0] + pi_width, pi_pos[1] + 1.9),
        'GPIO22 (Vibration)': (pi_pos[0] + pi_width, pi_pos[1] + 1.6),
        'GND': (pi_pos[0] + pi_width, pi_pos[1] + 1.3),
        '5V': (pi_pos[0] + pi_width, pi_pos[1] + 1.0),
        'CSI (Camera)': (pi_pos[0] + pi_width, pi_pos[1] + 0.7),
    }
    
    # Ajouter les broches GPIO
    for label, pos in gpio_pins.items():
        ax.add_patch(patches.Rectangle(pos, 0.2, 0.15, 
                                      facecolor='gold', edgecolor='black', lw=1, zorder=3))
        ax.text(pos[0] + 0.3, pos[1] + 0.075, label, 
                ha='left', va='center', fontsize=8)
    
    # Dessiner le capteur ultrasonique avec plus de détails
    # Corps du capteur
    ax.add_patch(patches.Rectangle(ultrasonic_pos, ultrasonic_width, ultrasonic_height, 
                                  facecolor=COLORS['ultrasonic'], 
                                  edgecolor='black', lw=2, zorder=2))
    
    # Les deux "yeux" du capteur ultrasonique
    eye_radius = 0.2
    eye_y = ultrasonic_pos[1] + ultrasonic_height/2
    
    # Œil gauche (émetteur)
    ax.add_patch(patches.Circle((ultrasonic_pos[0] + 0.5, eye_y), eye_radius, 
                               facecolor='silver', edgecolor='black', lw=1, zorder=3))
    
    # Œil droit (récepteur)
    ax.add_patch(patches.Circle((ultrasonic_pos[0] + ultrasonic_width - 0.5, eye_y), eye_radius, 
                               facecolor='silver', edgecolor='black', lw=1, zorder=3))
    
    # Étiquette pour le capteur ultrasonique
    ax.text(ultrasonic_pos[0] + ultrasonic_width/2, ultrasonic_pos[1] + ultrasonic_height/2, 
            'Capteur\nultrasonique\nHC-SR04',
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Broches du capteur ultrasonique
    us_pins = {
        'Trig': (ultrasonic_pos[0], ultrasonic_pos[1] + 0.8),
        'Echo': (ultrasonic_pos[0], ultrasonic_pos[1] + 0.6),
        'GND': (ultrasonic_pos[0], ultrasonic_pos[1] + 0.4),
        'VCC': (ultrasonic_pos[0], ultrasonic_pos[1] + 0.2),
    }
    
    # Ajouter les broches du capteur ultrasonique
    for label, pos in us_pins.items():
        ax.add_patch(patches.Rectangle(pos, 0.2, 0.15, 
                                      facecolor='gold', edgecolor='black', lw=1, zorder=3))
        ax.text(pos[0] - 0.3, pos[1] + 0.075, label, 
                ha='right', va='center', fontsize=8)
    
    # Dessiner le moteur de vibration avec plus de détails
    # Corps du moteur
    ax.add_patch(patches.Rectangle(vibration_pos, vibration_width, vibration_height, 
                                  facecolor=COLORS['vibration'], 
                                  edgecolor='black', lw=2, zorder=2))
    
    # Forme du moteur (cercle à l'intérieur)
    motor_center = (vibration_pos[0] + vibration_width/2, vibration_pos[1] + vibration_height/2)
    ax.add_patch(patches.Circle(motor_center, 0.3, 
                               facecolor='silver', edgecolor='black', lw=1, zorder=3, alpha=0.8))
    
    # Axe du moteur
    ax.add_patch(patches.Circle(motor_center, 0.05, 
                               facecolor='black', edgecolor='black', lw=1, zorder=4))
    
    # Fils du moteur
    motor_wire_start = (vibration_pos[0], vibration_pos[1] + 0.3)
    
    # Étiquette pour le moteur de vibration
    ax.text(vibration_pos[0] + vibration_width/2, vibration_pos[1] + vibration_height + 0.2, 
            'Moteur de vibration',
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Dessiner la caméra avec plus de détails
    # Corps de la caméra
    ax.add_patch(patches.Rectangle(camera_pos, camera_width, camera_height, 
                                  facecolor=COLORS['camera'], 
                                  edgecolor='black', lw=2, zorder=2))
    
    # Objectif de la caméra
    lens_center = (camera_pos[0] + 0.3, camera_pos[1] + camera_height/2)
    ax.add_patch(patches.Circle(lens_center, 0.2, 
                               facecolor='black', edgecolor='silver', lw=2, zorder=3))
    
    # Reflet de l'objectif
    ax.add_patch(patches.Circle((lens_center[0] - 0.05, lens_center[1] + 0.05), 0.05, 
                               facecolor='white', edgecolor=None, zorder=4, alpha=0.6))
    
    # Carte électronique de la caméra
    ax.add_patch(patches.Rectangle((camera_pos[0] + 0.6, camera_pos[1] + 0.2), 
                                  0.7, 0.6, 
                                  facecolor='green', edgecolor='black', lw=1, zorder=3, alpha=0.8))
    
    # Étiquette pour la caméra
    ax.text(camera_pos[0] + camera_width/2, camera_pos[1] + camera_height + 0.2, 
            'Caméra Raspberry Pi',
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Dessiner les smartphones (pour montrer la connectivité)
    # Smartphone 1 (connexion Bluetooth)
    bt_smartphone_pos = (1.5, 6)
    bt_connection = draw_smartphone(ax, bt_smartphone_pos, label="Smartphone\n(Bluetooth)")
    
    # Smartphone 2 (connexion WiFi)
    wifi_smartphone_pos = (1.5, 3)
    wifi_connection = draw_smartphone(ax, wifi_smartphone_pos, label="Smartphone\n(WiFi)")
    
    # Smartphone 3 (connexion USB)
    usb_smartphone_pos = (1.5, 0.5)
    usb_connection = draw_smartphone(ax, usb_smartphone_pos, label="Smartphone\n(USB)")
    
    # Dessiner les icônes de connexion
    # Icône Bluetooth
    bt_icon_pos = (3.5, 6.5)
    draw_connection_icon(ax, bt_icon_pos, 'bluetooth', label="Bluetooth")
    
    # Icône WiFi
    wifi_icon_pos = (3.5, 3.5)
    draw_connection_icon(ax, wifi_icon_pos, 'wifi', label="WiFi/API REST")
    
    # Icône USB
    usb_icon_pos = (3.5, 1)
    draw_connection_icon(ax, usb_icon_pos, 'usb', label="USB")
    
    # Dessiner les fils de connexion avec annotations
    # Capteur ultrasonique -> Raspberry Pi
    draw_wire(ax, us_pins['Trig'], gpio_pins['GPIO17 (Trig)'], 'red', lw=2, annotate="Signal de déclenchement")
    draw_wire(ax, us_pins['Echo'], gpio_pins['GPIO27 (Echo)'], 'blue', lw=2, annotate="Réception de l'écho")
    draw_wire(ax, us_pins['GND'], gpio_pins['GND'], 'black', lw=2, annotate="Masse commune")
    draw_wire(ax, us_pins['VCC'], gpio_pins['5V'], 'red', lw=2, annotate="Alimentation 5V")
    
    # Moteur de vibration -> Raspberry Pi
    draw_wire(ax, (vibration_pos[0], vibration_pos[1] + vibration_height/2), 
             gpio_pins['GPIO22 (Vibration)'], 'orange', lw=2, annotate="Contrôle de vibration")
    draw_wire(ax, (vibration_pos[0], vibration_pos[1] + vibration_height/4), 
             (gpio_pins['GND'][0], gpio_pins['GND'][1] - 0.2), 'black', lw=2)
    
    # Caméra -> Raspberry Pi
    draw_wire(ax, (camera_pos[0], camera_pos[1] + camera_height/2),
             gpio_pins['CSI (Camera)'], 'gray', lw=3, annotate="Connexion CSI")
    
    # Connexions sans fil aux smartphones
    # Bluetooth
    draw_wire(ax, bt_connection, bt_connection_point, COLORS['bluetooth'], lw=2, 
             style='--', curve_height=1, annotate="Communication Bluetooth")
    
    # WiFi
    draw_wire(ax, wifi_connection, wifi_connection_point, COLORS['wifi'], lw=2, 
             style='-.', curve_height=0.7, annotate="Communication Wi-Fi (API REST)")
    
    # USB
    draw_wire(ax, usb_connection, usb_connection_point, COLORS['usb'], lw=2, 
             curve_height=0.8, annotate="Connexion USB directe")
    
    # Légende pour les types de fils
    legend_x, legend_y = 12, 8
    legend_spacing = 0.4
    
    # Titre de la légende
    ax.text(legend_x, legend_y + 0.5, 'Légende des connexions:', fontsize=12, fontweight='bold')
    
    # Fils pour la légende
    wire_labels = [
        ('Signal Trig (GPIO17)', 'red'),
        ('Signal Echo (GPIO27)', 'blue'),
        ('Alimentation 5V', 'red'),
        ('Masse (GND)', 'black'),
        ('Signal Vibration (GPIO22)', 'orange'),
        ('Connexion Caméra (CSI)', 'gray'),
        ('Bluetooth', COLORS['bluetooth']),
        ('WiFi (API REST)', COLORS['wifi']),
        ('USB', COLORS['usb']),
    ]
    
    # Ajouter la légende des fils
    for i, (label, color) in enumerate(wire_labels):
        y_pos = legend_y - i * legend_spacing
        
        # Style de ligne selon le type de connexion
        line_style = '-'
        if 'Bluetooth' in label:
            line_style = '--'
        elif 'WiFi' in label:
            line_style = '-.'
            
        ax.plot([legend_x, legend_x + 0.5], [y_pos, y_pos], color=color, lw=2, linestyle=line_style)
        ax.text(legend_x + 0.7, y_pos, label, va='center', fontsize=10)
    
    # Légende pour les composants
    component_x = legend_x
    component_y = legend_y - (len(wire_labels) + 0.5) * legend_spacing
    
    # Titre de la section
    ax.text(component_x, component_y, 'Composants:', fontsize=12, fontweight='bold')
    
    # Liste des composants pour la légende
    component_labels = [
        ('Raspberry Pi 4', COLORS['raspberry_pi']),
        ('Capteur ultrasonique HC-SR04', COLORS['ultrasonic']),
        ('Moteur de vibration', COLORS['vibration']),
        ('Caméra Raspberry Pi', COLORS['camera']),
        ('Smartphone (connecté)', COLORS['phone']),
    ]
    
    # Ajouter la légende des composants
    for i, (label, color) in enumerate(component_labels):
        y_pos = component_y - (i + 1) * legend_spacing
        ax.add_patch(patches.Rectangle((component_x, y_pos - 0.15), 0.3, 0.3, 
                                      facecolor=color, edgecolor='black', lw=1))
        ax.text(component_x + 0.7, y_pos, label, va='center', fontsize=10)
    
    # Ajouter une section explicative sur les connexions
    connection_x = 12
    connection_y = 2.5
    
    # Titre de la section
    ax.text(connection_x, connection_y, 'Modes de connexion:', fontsize=12, fontweight='bold')
    
    # Description des connexions
    connection_descriptions = [
        "• Bluetooth: Communication sans fil directe avec le",
        "  smartphone. Portée d'environ 10 mètres.",
        "• WiFi: Communication via API REST sur réseau WiFi",
        "  ou Internet. Portée selon la couverture réseau.",
        "• USB: Connexion directe par câble USB entre le",
        "  Raspberry Pi et le smartphone. Plus fiable et stable."
    ]
    
    # Ajouter les descriptions des connexions
    for i, desc in enumerate(connection_descriptions):
        y_pos = connection_y - (i + 1) * 0.35
        ax.text(connection_x, y_pos, desc, va='center', fontsize=9)
    
    # Configurer les limites de l'axe
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 10)
    
    # Supprimer les graduations
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Ajouter un titre
    ax.set_title('Schéma de câblage complet - Système Canne intelligent pour malvoyants', 
                fontsize=18, fontweight='bold', pad=20)
    
    # Ajouter une note explicative
    note_text = (
        "Ce schéma illustre les connexions matérielles et les méthodes de communication du système Canne. "
        "Le capteur ultrasonique détecte les obstacles à distance, la caméra reconnaît les objets environnants, "
        "et le moteur de vibration fournit un retour haptique à l'utilisateur. "
        "Trois options de connectivité sont disponibles pour les smartphones: Bluetooth, WiFi (API REST) et connexion USB directe."
    )
    
    plt.figtext(0.5, 0.02, note_text, ha='center', fontsize=10, wrap=True,
               bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.8'),
               linespacing=1.5)
    
    # Ajouter des flèches explicatives
    # Flèche vers le capteur ultrasonique
    ax.annotate(
        "Mesure la distance\ndes obstacles (1-300 cm)",
        xy=(ultrasonic_pos[0] + ultrasonic_width/2, ultrasonic_pos[1] - 0.2),
        xytext=(ultrasonic_pos[0] + ultrasonic_width/2, ultrasonic_pos[1] - 0.8),
        ha='center',
        va='top',
        fontsize=9,
        arrowprops=dict(
            arrowstyle='->',
            color='black',
            lw=1,
            connectionstyle='arc3,rad=0.1'
        ),
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8)
    )
    
    # Flèche vers le moteur de vibration
    ax.annotate(
        "Retour haptique pour\nalerter l'utilisateur",
        xy=(vibration_pos[0] - 0.2, vibration_pos[1] + vibration_height/2),
        xytext=(vibration_pos[0] - 1.5, vibration_pos[1] + vibration_height/2),
        ha='right',
        va='center',
        fontsize=9,
        arrowprops=dict(
            arrowstyle='->',
            color='black',
            lw=1,
            connectionstyle='arc3,rad=0.1'
        ),
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8)
    )
    
    # Flèche vers la caméra
    ax.annotate(
        "Identifie les objets\net obstacles environnants",
        xy=(camera_pos[0] - 0.2, camera_pos[1] + camera_height/2),
        xytext=(camera_pos[0] - 1.5, camera_pos[1] + camera_height/2),
        ha='right',
        va='center',
        fontsize=9,
        arrowprops=dict(
            arrowstyle='->',
            color='black',
            lw=1,
            connectionstyle='arc3,rad=-0.1'
        ),
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8)
    )
    
    # Enregistrer l'image
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wiring_diagram.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Schéma de câblage complet généré et enregistré à : {output_file}")

if __name__ == "__main__":
    create_wiring_diagram() 