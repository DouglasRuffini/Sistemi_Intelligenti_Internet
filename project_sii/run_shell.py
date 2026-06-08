import sys
import os

# Assicura la corretta risoluzione dei moduli interni
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.ingestion.downloader import AdaptiveDownloader
from src.processing.extractor import InformationExtractor
from src.processing.verifier import PipelineVerifier
from src.utils.metrics import SemanticsEngine
from src.learning.clusterer import IntelligenceClusterer

def show_menu():
    print("\n" + "="*60)
    print("SISTEMA INTELLIGENTE DI INFORMATION EXTRACTION & TEXT MINING (SII)")
    print("Autore: Douglas Ruffini - Mat: 482379")
    print("="*60)
    print("1. Esegui intera pipeline automaticamente")
    print("2. Scarica nuovi dati (Ingestion)")
    print("3. Estrai informazioni da fonti scaricate (Processing)")
    print("4. Rianalizza directory ed esegui Clustering (Learning)")
    print("0. Esci")
    print("="*60)

def downloading(downloader, target_query, specific_query, index):

    if index == 1:
        downloader.clear_previous_sessions()    
    elif index == 2:
        # Download di massa per superare abbondantemente i 100 articoli totali reali
        downloader.fetch_arxiv_and_ar5iv(target_query)
        downloader.fetch_zenodo(target_query)
        downloader.fetch_nasa_ads(specific_query)
        downloader.fetch_noaa(target_query)
        downloader.fetch_openaire(target_query)
        downloader.fetch_figshare(target_query)
        downloader.fetch_kaggle(target_query)
    elif index == 3:
        downloader.generate_readme(target_query, specific_query)
   
    return True

def main():
    downloader = AdaptiveDownloader()
    extractor = InformationExtractor()
    verifier = PipelineVerifier()
    engine = SemanticsEngine()
    clusterer = IntelligenceClusterer()
    
    target_query = 'thunderstorm neutron "Terrestrial Gamma-ray Flash" lightning'
    specific_query = 'neutron thunderstorm'


    while True:
        show_menu()
        scelta = input("Seleziona un'opzione [0-4]: ").strip()
        
        if scelta == "1":
            # Sostituisci la query vecchia con questa variante pulita per le API esterne        
            print("\n[Pipeline] Inizializzazione Ambiente...")
            # FARE QUESTO PRIMA DI OGNI COSA: Cancella i risultati e gli archivi precedenti
            downloading(downloader, target_query, specific_query, 1)
            
            print("\n[Pipeline] Avvio dell'Ingestion Layer Multi-Sorgente...")
            # Chiamata a sub routin
            downloading(downloader, target_query, specific_query, 2)
            # Generazione log
            downloading(downloader, target_query, specific_query, 3)
                
            print("\n[Pipeline] Avvio del Processing Layer (Information Extraction)...")
            for file in os.listdir("data/sources/"):
                if file.endswith((".txt", ".html")):
                    extractor.analyze_file(file)
            
            print("\n[Pipeline] Avvio del Verifier e calcolo metriche...")
            verifier.generate_summary()
            engine.calculate_correlations()
            
            print("\n[Pipeline] Avvio del modulo di Learning (Clustering non supervisionato)...")
            clusterer.perform_clustering(n_clusters=2)
            
            print("\n" + "="*60)
            print("PIPELINE STRUTTURATA E COMPLETATA CON SUCCESSO!")
            print("Verificare i file estratti in 'data/extracted/' e i grafici in 'reports/'")
            print("="*60)
            
        elif scelta == "2":
            query = input("Inserisci query di ricerca: ").strip()
    
            # Download di massa per superare abbondantemente i 100 articoli totali reali
            # Chiamata a sub routin
            downloading(downloader, query if query else target_query, query if query else specific_query, 2)
            
        elif scelta == "3":
            print("[Pipeline] Estrazione in corso da data/sources/...")
            for file in os.listdir("data/sources/"):
                if file.endswith(".txt"):
                    extractor.analyze_file(file)
            summary = verifier.generate_summary()
            print(f"[Processing] Analisi completata. File analizzati: {summary.get('n_files', 0)}")
            
        elif scelta == "4":
            print("[Pipeline] Elaborazione statistiche avanzate, grafici e clustering...")
            engine.calculate_correlations()
            clusterer.perform_clustering(n_clusters=2)
            
        elif scelta == "0":
            print("Chiusura dell'applicazione. Arrivederci Douglas.")
            break
        else:
            print("Opzione non valida. Riprova.")

if __name__ == "__main__":
    main()
