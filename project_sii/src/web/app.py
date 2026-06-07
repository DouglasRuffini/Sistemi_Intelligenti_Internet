import os
import sys
import json
import shutil
import time
import threading
import pandas as pd

import matplotlib
matplotlib.use('Agg') 

from flask import Flask, Response, render_template, jsonify, request, send_from_directory
from src.ingestion.downloader import AdaptiveDownloader  
from src.processing.extractor import InformationExtractor
from src.utils.metrics import SemanticsEngine
from src.learning.clusterer import IntelligenceClusterer

app = Flask(__name__, template_folder='templates', static_folder='static')

EXTRACTED_DIR = "data/extracted/"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
LOG_FILE = "pipeline.log"



TOTAL_EXPECTED_SOURCES = (AdaptiveDownloader.TOTALE)

PIPELINE_STATUS = {
    "running": False,
    "current_stage": "In attesa...",
    "progress": 0,
    "completed_tasks": []
}

class RealTimeLogInterceptor(object):
    def __init__(self, current_stdout):
        self.terminal = current_stdout

    def write(self, message):
        self.terminal.write(message)
        self.terminal.flush()
        clean_msg = message.replace('\r', '\n')
        if clean_msg.strip():
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(clean_msg)

    def flush(self):
        self.terminal.flush()

def get_stats():
    stats = {"total_sources": 0, "total_extracted": 0, "heatmap_exists": False}
    if os.path.exists("data/sources/"):
        stats["total_sources"] = len([f for f in os.listdir("data/sources/") if os.path.isfile(os.path.join("data/sources/", f))])
    if os.path.exists(EXTRACTED_DIR):
        stats["total_extracted"] = len([f for f in os.listdir(EXTRACTED_DIR) if f.endswith(".json") and f != "summary.json"])
    stats["heatmap_exists"] = os.path.exists(os.path.join(REPORTS_DIR, "correlation_heatmap.png"))
    return stats

def run_pipeline_worker(mode):
    global PIPELINE_STATUS
    PIPELINE_STATUS["running"] = True
    PIPELINE_STATUS["completed_tasks"] = []
    
    try:
        # FASE 1: INGESTION
        if mode == 'all' or mode == 'ingest':
            PIPELINE_STATUS["current_stage"] = "Fase 1: Ingestion Layer (Download File)"
            PIPELINE_STATUS["progress"] = 0
            
            print("[Reset] Pulizia iniziale directory...")
            # --- MODIFICA QUI: Cancella la vecchia heatmap subito all'avvio del reset ---
            old_heatmap = os.path.join(REPORTS_DIR, "correlation_heatmap.png")
            if os.path.exists(old_heatmap):
                try:
                    os.remove(old_heatmap)
                    print("[Reset] Vecchia heatmap rimossa dal disco.")
                except Exception as e:
                    print(f"[Reset][Avviso] Impossibile rimuovere vecchia heatmap: {e}")
            # -------------------------------------------------------------------------

            for folder in ["data/sources/", "data/extracted/"]:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
                os.makedirs(folder, exist_ok=True)
            
            # ... resto del codice del downloader (arXiv, Zenodo, ecc.) ...
            
            downloader = AdaptiveDownloader()
            target_query = 'thunderstorm neutron "Terrestrial Gamma-ray Flash" lightning'
            nasa_ads_query = 'thunderstorm AND neutron AND ("Terrestrial Gamma-ray Flash" OR lightning OR Gurevich OR Chilingarian)'
            
            print("[arXiv/ar5iv] Scaricamento in corso...")
            downloader.fetch_arxiv_and_ar5iv(target_query)
            PIPELINE_STATUS["completed_tasks"].append("Repository arXiv/ar5iv scaricato")
            
            print("[Zenodo] Scaricamento in corso...")
            downloader.fetch_zenodo(target_query)
            PIPELINE_STATUS["completed_tasks"].append("Repository Zenodo scaricato")
            
            print("[NASA ADS] Scaricamento in corso...")
            downloader.fetch_nasa_ads(nasa_ads_query)
            PIPELINE_STATUS["completed_tasks"].append("Repository NASA ADS scaricato")
            
            print("[NOAA] Scaricamento in corso...")
            downloader.fetch_noaa(target_query)
            PIPELINE_STATUS["completed_tasks"].append("Catalogo atmosferico NOAA scaricato")
            
            print("[OpenAIRE] Scaricamento in corso...")
            downloader.fetch_openaire(target_query)
            PIPELINE_STATUS["completed_tasks"].append("Grafo della Ricerca OpenAIRE sincronizzato")
            
            print("[Figshare] Scaricamento in corso...")
            downloader.fetch_figshare(target_query)
            PIPELINE_STATUS["completed_tasks"].append("Metadati Figshare estratti")
            
            print("[Kaggle_Data] Controllo fallback...")
            downloader.fetch_kaggle(target_query)
            downloader.generate_readme(target_query, nasa_ads_query)
            
            PIPELINE_STATUS["completed_tasks"].append("FASE 1: Ingestion Layer Completata")
            time.sleep(1)

        # FASE 2: PROCESSING
        if mode == 'all' or mode == 'process':
            PIPELINE_STATUS["current_stage"] = "Fase 2: Processing Layer (Information Extraction)"
            PIPELINE_STATUS["progress"] = 0
            
            if not os.path.exists("data/sources/") or not os.listdir("data/sources/"):
                print("[ERRORE] Nessun file sorgente trovato.")
                print("[DONE]")
                PIPELINE_STATUS["running"] = False
                return
                
            extractor = InformationExtractor()
            sources = sorted(os.listdir("data/sources/"))
            total_files = len(sources)
            
            print("[Pipeline] Avvio estrazione informazioni...")
            for idx, filename in enumerate(sources, start=1):
                extractor.analyze_file(filename)
                PIPELINE_STATUS["progress"] = int((idx / total_files) * 100)
                
                if idx % 10 == 0 or idx == total_files:
                    print(f" -> Elaborazione: {idx}/{total_files} file estratti...")
            
            PIPELINE_STATUS["completed_tasks"].append("FASE 2: Estrazione e Normalizzazione JSON Completata")
            time.sleep(1)

        # FASE 3: LEARNING & ANALYTICS
        if mode == 'all' or mode == 'learn':
            PIPELINE_STATUS["current_stage"] = "Fase 3: Analisi Semantica & Algoritmi AI"
            PIPELINE_STATUS["progress"] = 0
            
            engine = SemanticsEngine()
            engine.calculate_correlations()
            PIPELINE_STATUS["progress"] = 50
            
            corr_file = os.path.join(REPORTS_DIR, "semantic_correlation.csv")
            if os.path.exists(corr_file):
                df_corr = pd.read_csv(corr_file, index_col=0)
                print(f"[Analytics] Matrice:\n{df_corr.to_string()}")
            
            clusterer = IntelligenceClusterer()
            clusterer.perform_clustering(n_clusters=2)
            
            PIPELINE_STATUS["progress"] = 100
            PIPELINE_STATUS["completed_tasks"].append("FASE 3: Clustering K-Means e Matrice Semantica completati")

        print("[DONE]")
        PIPELINE_STATUS["current_stage"] = "Tutti i processi sono terminati con successo!"
    except Exception as e:
        print(f"[ERRORE CRITICO]: {str(e)}")
        print("[DONE]")
        PIPELINE_STATUS["current_stage"] = f"Blocco per Errore: {str(e)}"
    finally:
        PIPELINE_STATUS["running"] = False

@app.route('/')
def index():
    # Carica il file HTML reale salvato fisicamente su disco
    return render_template('index.html')

@app.route('/reports/<filename>')
def serve_reports(filename):
    return send_from_directory(REPORTS_DIR, filename)

@app.route('/api/run/pipeline', methods=['POST'])
def start_pipeline_thread():
    mode = request.args.get('mode', 'all')
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    global PIPELINE_STATUS
    PIPELINE_STATUS["running"] = True
    PIPELINE_STATUS["progress"] = 0
    PIPELINE_STATUS["current_stage"] = "Fase 1: Ingestion Layer (Download File)"
    PIPELINE_STATUS["completed_tasks"] = []

    t = threading.Thread(target=run_pipeline_worker, args=(mode,))
    t.start()
    return jsonify({"status": "Thread attivato correttamente"})

@app.route('/api/status')
def get_pipeline_status():
    global PIPELINE_STATUS
    return jsonify({
        "running": PIPELINE_STATUS["running"],
        "current_stage": PIPELINE_STATUS["current_stage"],
        "progress": PIPELINE_STATUS["progress"],
        "completed_tasks": PIPELINE_STATUS["completed_tasks"],
        "total_expected": TOTAL_EXPECTED_SOURCES,
        "stats": get_stats()
    })

@app.route('/api/logs/live')
def read_live_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return Response(f.read(), mimetype='text/plain')
    return Response("", mimetype='text/plain')

if __name__ == '__main__':
    sys.stdout = RealTimeLogInterceptor(sys.stdout)
    app.run(debug=True, port=5000, use_reloader=False)