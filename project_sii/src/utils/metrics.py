import os
import json
import pandas as pd
import numpy as np

class SemanticsEngine:
    def __init__(self, extracted_dir="data/extracted/"):
        self.extracted_dir = extracted_dir

    def calculate_correlations(self, output_path="reports/"):
        os.makedirs(output_path, exist_ok=True)
        files = [f for f in os.listdir(self.extracted_dir) if f.endswith(".json") and f != "summary.json"]
        
        if not files:
            return
            
        data_list = []
        for file in files:
            with open(os.path.join(self.extracted_dir, file), "r", encoding="utf-8") as f:
                js = json.load(f)
            data_list.append(js["semantic_metrics"])
            
        df = pd.DataFrame(data_list)
        
        # Generazione del file CSV delle frequenze cumulate
        df.to_csv(os.path.join(output_path, "semantic_counts.csv"), index=False)
        
        # Calcolo della matrice di correlazione di Pearson per mappare il vuoto semantico
        corr_matrix = df.corr(method='pearson').fillna(0)
        corr_matrix.to_csv(os.path.join(output_path, "semantic_correlation.csv"))
        
        print(f"[Analytics] Generata matrice di correlazione in {output_path}semantic_correlation.csv")
        print(corr_matrix)
        
        # Creazione programmatica della Heatmap grafica usando solo matplotlib/pandas per evitare fallimenti ambientali
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            plt.figure(figsize=(6,4))
            sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", vmin=-1, vmax=1)
            plt.title("Mappa di Correlazione Semantica (Mappatura TA / SII)")
            plt.tight_layout()
            plt.savefig(os.path.join(output_path, "correlation_heatmap.png"))
            plt.close()
            print("[Analytics] Grafico 'correlation_heatmap.png' salvato con successo.")
        except Exception as e:
            print(f"[WARNING Analytics] Impossibile generare la heatmap grafica: {e}")