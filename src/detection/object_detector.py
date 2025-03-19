"""
Module pour la détection d'objets utilisant OpenCV et le modèle MobileNet SSD.
"""

import os
import cv2
import logging
import numpy as np

# Configuration du logger
logger = logging.getLogger(__name__)

class ObjectDetector:
    """Classe pour la détection d'objets avec OpenCV et MobileNet SSD."""
    
    def __init__(self, model_dir, confidence_threshold=0.5, max_detections=5):
        """
        Initialise le détecteur d'objets.
        
        Args:
            model_dir (str): Chemin vers le répertoire contenant le modèle
            confidence_threshold (float): Seuil de confiance pour la détection (0.0 à 1.0)
            max_detections (int): Nombre maximal d'objets à renvoyer
        """
        self.model_dir = model_dir
        self.confidence_threshold = confidence_threshold
        self.max_detections = max_detections
        
        # Charger le modèle de détection
        try:
            # Chemins des fichiers de modèle
            model_path = os.path.join(model_dir, 'frozen_inference_graph.pb')
            config_path = os.path.join(model_dir, 'ssd_mobilenet_v2_coco_2018_03_29.pbtxt')
            
            # Vérifier l'existence des fichiers
            if not os.path.exists(model_path) or not os.path.exists(config_path):
                raise FileNotFoundError(f"Fichiers de modèle introuvables dans: {model_dir}")
            
            # Charger le modèle avec OpenCV DNN
            self.net = cv2.dnn.readNetFromTensorflow(model_path, config_path)
            
            # Charger les labels
            labels_path = os.path.join(model_dir, 'coco_class_labels.txt')
            if os.path.exists(labels_path):
                with open(labels_path, 'r') as f:
                    self.class_labels = [line.strip() for line in f.readlines()]
            else:
                logger.warning(f"Fichier de labels introuvable: {labels_path}")
                self.class_labels = []
            
            logger.info("Détecteur d'objets initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du détecteur d'objets: {e}")
            raise
    
    def detect_objects(self, frame):
        """
        Détecte les objets dans une image.
        
        Args:
            frame (numpy.ndarray): Image au format OpenCV (BGR)
            
        Returns:
            list: Liste de tuples (classe, confiance, boîte) des objets détectés
        """
        if frame is None or frame.size == 0:
            logger.warning("Image vide ou invalide fournie pour la détection")
            return []
        
        try:
            # Obtenir les dimensions de l'image
            height, width = frame.shape[:2]
            
            # Préparer l'image pour le réseau de neurones (blob)
            blob = cv2.dnn.blobFromImage(
                cv2.resize(frame, (300, 300)),
                0.007843, (300, 300), 127.5
            )
            
            # Passer le blob à travers le réseau
            self.net.setInput(blob)
            detections = self.net.forward()
            
            # Traiter les détections
            results = []
            for i in range(detections.shape[2]):
                # Extraire la confiance de la détection
                confidence = detections[0, 0, i, 2]
                
                # Filtrer les détections faibles
                if confidence > self.confidence_threshold:
                    # Obtenir l'indice de classe
                    class_id = int(detections[0, 0, i, 1])
                    
                    # Obtenir les coordonnées de la boîte englobante
                    box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
                    (startX, startY, endX, endY) = box.astype("int")
                    
                    # Obtenir le nom de la classe
                    if 0 <= class_id < len(self.class_labels):
                        class_name = self.class_labels[class_id]
                    else:
                        class_name = f"Classe-{class_id}"
                    
                    # Ajouter la détection aux résultats
                    results.append((class_name, confidence, (startX, startY, endX, endY)))
            
            # Trier les résultats par confiance (du plus élevé au plus bas)
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Limiter le nombre de détections retournées
            results = results[:self.max_detections]
            
            logger.debug(f"{len(results)} objets détectés")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'objets: {e}")
            return []
    
    def annotate_frame(self, frame, detections):
        """
        Annote le cadre avec les boîtes englobantes et les étiquettes.
        
        Args:
            frame (numpy.ndarray): Image au format OpenCV (BGR)
            detections (list): Liste de tuples (classe, confiance, boîte)
            
        Returns:
            numpy.ndarray: Image annotée
        """
        # Créer une copie de l'image
        annotated = frame.copy()
        
        for (class_name, confidence, (x_min, y_min, x_max, y_max)) in detections:
            # Dessiner la boîte englobante
            cv2.rectangle(annotated, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            
            # Préparer le texte de l'étiquette
            label = f"{class_name}: {confidence:.2f}"
            
            # Calculer la taille du texte
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            # Dessiner l'arrière-plan de l'étiquette
            cv2.rectangle(annotated, (x_min, y_min - text_size[1] - 10), 
                          (x_min + text_size[0], y_min), (0, 255, 0), -1)
            
            # Dessiner le texte
            cv2.putText(annotated, label, (x_min, y_min - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return annotated
    
    def get_detection_summary(self, detections):
        """
        Crée un résumé textuel des objets détectés.
        
        Args:
            detections (list): Liste de tuples (classe, confiance, boîte)
            
        Returns:
            str: Résumé des objets détectés
        """
        if not detections:
            return "Aucun objet détecté."
        
        # Compter les occurrences de chaque classe
        class_counts = {}
        for class_name, _, _ in detections:
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        # Créer le résumé
        summary_parts = []
        for class_name, count in class_counts.items():
            if count == 1:
                summary_parts.append(f"un {class_name}")
            else:
                summary_parts.append(f"{count} {class_name}s")
        
        if len(summary_parts) == 1:
            return f"Détecté: {summary_parts[0]}."
        elif len(summary_parts) == 2:
            return f"Détecté: {summary_parts[0]} et {summary_parts[1]}."
        else:
            last_part = summary_parts.pop()
            return f"Détecté: {', '.join(summary_parts)} et {last_part}."


def test_detector():
    """Fonction de test pour le détecteur d'objets."""
    import time
    import os
    
    try:
        # Configuration du logging pour le test
        logging.basicConfig(level=logging.INFO)
        
        # Chemin du modèle (à ajuster selon votre installation)
        model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                "models", "mobilenet_ssd")
        
        # Vérifier si le modèle existe
        if not os.path.exists(model_dir):
            print(f"Répertoire de modèle introuvable: {model_dir}")
            print("Veuillez exécuter setup.sh pour télécharger le modèle")
            return
        
        # Initialiser le détecteur
        detector = ObjectDetector(model_dir)
        
        # Initialiser la caméra
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Impossible d'ouvrir la caméra")
            return
        
        print("Test du détecteur d'objets. Appuyez sur 'q' pour quitter.")
        
        while True:
            # Capturer l'image
            ret, frame = cap.read()
            if not ret:
                print("Erreur lors de la capture de l'image")
                break
            
            # Détecter les objets
            start_time = time.time()
            detections = detector.detect_objects(frame)
            elapsed = time.time() - start_time
            
            # Annoter l'image
            annotated = detector.annotate_frame(frame, detections)
            
            # Afficher les FPS
            fps = 1.0 / elapsed if elapsed > 0 else 0
            cv2.putText(annotated, f"FPS: {fps:.1f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Afficher l'image
            cv2.imshow('Object Detection', annotated)
            
            # Afficher le résumé
            summary = detector.get_detection_summary(detections)
            print(f"\r{summary}", end="")
            
            # Quitter si 'q' est pressé
            if cv2.waitKey(1) == ord('q'):
                break
        
        # Nettoyer
        cap.release()
        cv2.destroyAllWindows()
        print("\nTest terminé.")
            
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur")
    except Exception as e:
        print(f"\nErreur: {e}")
    finally:
        if 'cap' in locals() and cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    test_detector() 