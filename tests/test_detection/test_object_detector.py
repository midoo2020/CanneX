"""
Tests unitaires pour le module de détection d'objets.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import numpy as np
import cv2
from src.detection.object_detector import ObjectDetector

class TestObjectDetector(unittest.TestCase):
    """Tests pour la classe ObjectDetector."""
    
    @patch('cv2.dnn.readNetFromTensorflow')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="personne\nvoiture\nchaise\n")
    def setUp(self, mock_file, mock_exists, mock_read_net):
        """Configuration avant chaque test."""
        # Configurer les mocks
        mock_exists.return_value = True
        self.mock_net = MagicMock()
        mock_read_net.return_value = self.mock_net
        
        # Paramètres du détecteur
        self.model_dir = "/fake/path/to/model"
        self.confidence_threshold = 0.6
        self.max_detections = 3
        
        # Créer une instance du détecteur
        self.detector = ObjectDetector(
            model_dir=self.model_dir,
            confidence_threshold=self.confidence_threshold,
            max_detections=self.max_detections
        )
        
        # Vérifier que le modèle a été chargé correctement
        mock_read_net.assert_called_once()
        
        # Vérifier que les labels ont été chargés
        self.assertEqual(len(self.detector.class_labels), 3)
        self.assertEqual(self.detector.class_labels[0], "personne")
    
    def test_init_with_missing_files(self):
        """Teste l'initialisation avec des fichiers manquants."""
        with patch('os.path.exists', return_value=False):
            with self.assertRaises(FileNotFoundError):
                ObjectDetector(model_dir=self.model_dir)
    
    def test_detect_objects_empty_frame(self):
        """Teste la détection avec une image vide."""
        # Appeler la méthode avec une image vide (None)
        result = self.detector.detect_objects(None)
        
        # Vérifier que le résultat est une liste vide
        self.assertEqual(result, [])
        
        # Appeler la méthode avec une image de taille zéro
        empty_frame = np.array([])
        result = self.detector.detect_objects(empty_frame)
        
        # Vérifier que le résultat est une liste vide
        self.assertEqual(result, [])
    
    @patch('cv2.dnn.blobFromImage')
    def test_detect_objects(self, mock_blob_from_image):
        """Teste la détection d'objets."""
        # Créer une image de test
        test_frame = np.zeros((300, 300, 3), dtype=np.uint8)
        
        # Configurer le mock pour blobFromImage
        mock_blob = MagicMock()
        mock_blob_from_image.return_value = mock_blob
        
        # Configurer la sortie simulée du réseau de neurones
        # Format: [[[class_id, confidence, x1, y1, x2, y2]]]
        # Simuler 3 détections: une personne avec confiance élevée,
        # une voiture avec confiance moyenne, une chaise avec confiance faible
        mock_detections = np.array([[[[
            [0, 0, 0],  # Placeholder
            [0, 1, 0.8, 0.1, 0.1, 0.5, 0.5],  # Personne (class_id=1, conf=0.8)
            [0, 2, 0.7, 0.2, 0.2, 0.6, 0.6],  # Voiture (class_id=2, conf=0.7) 
            [0, 3, 0.5, 0.3, 0.3, 0.7, 0.7]   # Chaise (class_id=3, conf=0.5) - sous le seuil
        ]]]])
        
        # La méthode forward du réseau retourne les détections simulées
        self.mock_net.forward.return_value = mock_detections
        
        # Appeler la méthode à tester
        results = self.detector.detect_objects(test_frame)
        
        # Vérifier que le réseau a été utilisé correctement
        self.mock_net.setInput.assert_called_once_with(mock_blob)
        self.mock_net.forward.assert_called_once()
        
        # Vérifier les résultats (seulement 2 détections devraient dépasser le seuil)
        self.assertEqual(len(results), 2)
        
        # Vérifier le tri par confiance (personne d'abord, puis voiture)
        self.assertEqual(results[0][0], "personne")
        self.assertEqual(results[1][0], "voiture")
        
        # Vérifier les valeurs de confiance
        self.assertAlmostEqual(results[0][1], 0.8)
        self.assertAlmostEqual(results[1][1], 0.7)
    
    def test_annotate_frame(self):
        """Teste l'annotation d'une image avec les détections."""
        # Créer une image de test
        test_frame = np.zeros((300, 300, 3), dtype=np.uint8)
        
        # Créer des détections simulées
        detections = [
            ("personne", 0.8, (50, 50, 150, 150)),
            ("voiture", 0.7, (100, 100, 200, 200))
        ]
        
        # Appeler la méthode à tester
        annotated = self.detector.annotate_frame(test_frame, detections)
        
        # Vérifier que l'image retournée n'est pas la même (une copie modifiée)
        self.assertIsNot(annotated, test_frame)
        
        # Vérifier que l'image annotée est différente de l'image originale
        # Note: Nous ne pouvons pas facilement vérifier les dessins exacts, mais au moins
        # nous pouvons vérifier que l'image a été modifiée
        self.assertFalse(np.array_equal(annotated, test_frame))
    
    def test_get_detection_summary_empty(self):
        """Teste le résumé de détection vide."""
        # Appeler la méthode avec une liste vide
        summary = self.detector.get_detection_summary([])
        
        # Vérifier le message
        self.assertEqual(summary, "Aucun objet détecté.")
    
    def test_get_detection_summary_single(self):
        """Teste le résumé avec une seule détection."""
        # Créer une détection simulée
        detections = [("personne", 0.8, (50, 50, 150, 150))]
        
        # Appeler la méthode à tester
        summary = self.detector.get_detection_summary(detections)
        
        # Vérifier le message
        self.assertEqual(summary, "Détecté: un personne.")
    
    def test_get_detection_summary_multiple(self):
        """Teste le résumé avec plusieurs détections."""
        # Créer des détections simulées avec des doublons
        detections = [
            ("personne", 0.8, (50, 50, 150, 150)),
            ("personne", 0.7, (100, 100, 200, 200)),
            ("voiture", 0.9, (150, 150, 250, 250)),
            ("chaise", 0.6, (200, 200, 300, 300))
        ]
        
        # Appeler la méthode à tester
        summary = self.detector.get_detection_summary(detections)
        
        # Vérifier le message (format "Détecté: 2 personnes, un voiture et un chaise.")
        self.assertTrue("2 personnes" in summary)
        self.assertTrue("un voiture" in summary)
        self.assertTrue("un chaise" in summary)

if __name__ == '__main__':
    unittest.main() 