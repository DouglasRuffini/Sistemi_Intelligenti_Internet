import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

class IntelligenceClusterer:
    def __init__(self, extracted_dir="data/extracted/"):
        self.extracted_dir = extracted_dir

    def perform_clustering(self, n_clusters=2):
        """Esegue il clustering non supervisionato K-Means sul corpus estratto."""
        import os
        import json
        
        file_list = sorted(os.listdir(self.extracted_dir))
        corpus = []
        valid_files = []
        
        for filename in file_list:
            if not filename.endswith(".json"):
                continue
                
            with open(os.path.join(self.extracted_dir, filename), "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # SOLUZIONE: Recupero dinamico del testo in base a cosa ha estratto l'InformationExtractor
            text_content = ""
            
            # Caso 1: Se ci sono sezioni HTML (dati reali da arXiv)
            if "html_sections" in data:
                text_content += " ".join([sec.get("text", "") or sec.get("caption", "") for sec in data["html_sections"]])
            
            # Caso 2: Se c'e un'anteprima testuale (file piatti o fallback)
            if "raw_text_preview" in data:
                text_content += " " + data["raw_text_preview"]
                
            # Caso 3: Vecchio fallback o chiavi legacy (per retrocompatibilita)
            if "raw_text_clean" in data:
                text_content += " " + data["raw_text_clean"]
                
            # Se l'unione dei campi ha prodotto testo, lo inseriamo nel corpus per TF-IDF
            text_content = text_content.strip()
            if text_content:
                corpus.append(text_content)
                valid_files.append(filename)
            else:
                # Se e un file CSV puro senza testo ma con variabili, usiamo i nomi degli header come testo!
                if "csv_structure" in data:
                    csv_text = " ".join(data["csv_structure"].get("headers", []))
                    corpus.append(csv_text)
                    valid_files.append(filename)

        if not corpus:
            print("[Learning - ERROR] Corpus vuoto. Impossibile addestrare il K-Means.")
            return
            
        # ... Da qui in poi il tuo codice TF-IDF e KMeans (TfidfVectorizer, kmeans.fit, ecc.) continua normalmente ...