import os
import re
import json
import csv
from lxml import html

class InformationExtractor:
    def __init__(self, source_dir="data/sources/", output_dir="data/extracted/"):
        self.source_dir = source_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Unione pattern numerici e unita' di misura fisiche (dal tuo e mio script)
        self.numeric_unit_pattern = re.compile(
            r"(\d[\d\.\,]*[\s]?(?:[eE××][\+\-]?\d+)?)\s*(V/m|n/cm\^2/s|n/cm2/s|MeV|keV|μs|us|ns|ps|s|ms|kG|pT|T|A|Pa|K|n/s)",
            re.IGNORECASE
        )
        self.generic_numeric_regex = re.compile(r'\b\d+(?:\.\d+)?(?:e[+-]?\d+)?\b')
        
        # Parole chiave per identificare nodi HTML rilevanti (dal tuo script)
        self.ta_keywords = r"\b(neutron|gamma|flash|electric|field|discharge|tgf|tge|timing|delay|anomaly|burst)\b"
        
        # Thesaurus controllato per definire i domini di co-occorrenza semantica 
        # (Ottimizzato: rimosso l'inghippo del tokenizzatore)
        self.thesaurus = {
            "lightning": ["lightning", "thunder", "storm", "discharge", "plasma", "lightning-induced"],
            "electric": ["field", "charge", "current", "voltage", "breakdown", "potential"],
            "nuclear": ["neutron", "gamma", "flux", "radiation", "tgf", "tge", "burst"],
            "temporal": ["delay", "rc", "relaxation", "pulse", "transient", "lifetime", "timing"]
        }

    def _compute_semantic_metrics(self, text):
        """Calcola le frequenze dei termini del Thesaurus nel testo normalizzato."""
        clean_text = text.lower()
        counts = {category: 0 for category in self.thesaurus}
        for category, keywords in self.thesaurus.items():
            for kw in keywords:
                # Cerca il termine isolato come parola intera o come prefisso/suffisso comune
                counts[category] += len(re.findall(r'\b' + re.escape(kw) + r'\b', clean_text))
        return counts

    def process_html(self, path, filename):
        """Estrae dati strutturali (tabelle) e testo (paragrafi) usando lxml."""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        
        doc = html.fromstring(text)
        
        # Estrazione titolo dell'articolo HTML (se presente nei tag standard)
        title_tag = doc.xpath("//title/text() | //h1/text()")
        title = title_tag[0].strip() if title_tag else filename
        
        sections_data = []
        full_text_accumulator = title + " "
        explicit_units = []
        
        tables = doc.xpath("//table | //figure") 
        relevant_paras = doc.xpath(
            f"//p[re:match(., '{self.ta_keywords}', 'i') or contains(., 'Table') or contains(., 'Fig.')]", 
            namespaces={'re': 'http://exslt.org/regular-expressions'}
        )
        
        # Parsing Tabelle
        for idx, t in enumerate(tables, start=1):
            caption_text = (t.xpath(".//caption/text() | .//figcaption/text()") or [""])[0].strip()
            table_html = html.tostring(t, encoding='unicode', pretty_print=False)
            numeric_hits = self.numeric_unit_pattern.findall(caption_text)
            
            extracted_vals = [f"{val[0]} {val[1]}" for val in numeric_hits]
            explicit_units.extend(extracted_vals)
            full_text_accumulator += " " + caption_text
            
            sections_data.append({
                "id": f"id_table_{idx}",
                "caption": caption_text,
                "data_type": "table_html",
                "extracted_values": extracted_vals,
                "raw_html": table_html[:200] + "..." # Troncato per pulizia nel JSON finale
            })
            
        # Parsing Paragrafi rilevanti
        for idx, p in enumerate(relevant_paras):
            ptxt = p.text_content().strip()
            if len(ptxt) > 50:
                numeric_hits = self.numeric_unit_pattern.findall(ptxt)
                extracted_vals = [f"{val[0]} {val[1]}" for val in numeric_hits]
                explicit_units.extend(extracted_vals)
                full_text_accumulator += " " + ptxt
                
                sections_data.append({
                    "id": f"id_paragraph_{idx}",
                    "text": ptxt,
                    "data_type": "text_paragraph",
                    "extracted_values": extracted_vals,
                })
        
        # Calcoli analitici aggregati per il modulo di Clustering
        all_numbers = self.generic_numeric_regex.findall(full_text_accumulator)
        semantic_metrics = self._compute_semantic_metrics(full_text_accumulator)
        
        return {
            "source": "arXiv/ar5iv (HTML Engine)",
            "title": title,
            "filename": filename,
            "variables_found": list(set(explicit_units)),
            "semantic_metrics": semantic_metrics,
            "stats": {
                "total_numbers": len(all_numbers),
                "suspect_numbers": max(0, len(all_numbers) - len(explicit_units))
            },
            "html_sections": sections_data
        }

    def process_csv_txt(self, path, filename):
        """Estrae dati tabellari strutturati tramite Sniffer o analizza il testo grezzo (Fallback)."""
        
        # 1. Apriamo il file in modo sicuro ed estraiamo subito sia la preview che il corpo intero
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            first_lines = [f.readline() for _ in range(5)]
            f.seek(0)  # Riposizioniamo il cursore all'inizio
            full_body_content = f.read()  # Leggiamo tutto mentre il file è aperto!
            
        content_preview = "".join(first_lines)
        
        # Rilevamento intestazioni "Title: " tipiche dei fallback sintetici o file txt piatti
        if "Title:" in content_preview:
            # Pulizia e parsing delle righe chiave basandoci sul contenuto completo appena letto
            lines = full_body_content.split("\n")
            title = lines[0].replace("Title: ", "").strip() if lines else "Unknown"
            source = "Local Repository"
            
            for line in lines[:3]:
                if "Source:" in line:
                    source = line.replace("Source: ", "").strip()
            
            explicit_units = [f"{v[0]} {v[1]}" for v in self.numeric_unit_pattern.findall(full_body_content)]
            all_numbers = self.generic_numeric_regex.findall(full_body_content)
            semantic_metrics = self._compute_semantic_metrics(full_body_content)
            
            return {
                "source": source,
                "title": title,
                "filename": filename,
                "variables_found": explicit_units,
                "semantic_metrics": semantic_metrics,
                "stats": {
                    "total_numbers": len(all_numbers),
                    "suspect_numbers": max(0, len(all_numbers) - len(explicit_units))
                },
                "raw_text_preview": full_body_content[:400] + "..."
            }
            
        # 2. Se non è un file piatto/fallback, procedi con il parsing del dataset CSV reale (Algoritmo Sniffer)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                try:
                    dialect = csv.Sniffer().sniff(content[:2048], delimiters=',;')
                except csv.Error:
                    dialect = 'excel'
                
                f.seek(0)
                reader = csv.reader(f, dialect)
                header = next(reader)
                
                preview_rows = []
                for i, row in enumerate(reader):
                    if i < 10:
                        preview_rows.append(row)
                    else:
                        break
                
                analyzed_variables = []
                combined_headers_text = " ".join(header)
                
                for h in header:
                    match = re.search(r'\(([^)]+)\)', h)
                    unit = match.group(1).strip() if match else ""
                    is_ta_relevant = bool(re.search(self.ta_keywords, h, re.IGNORECASE))
                    analyzed_variables.append({"name": h, "unit": unit, "is_ta_relevant": is_ta_relevant})
            
            # Uniamo intestazioni e anteprime per calcolare la semantica del dataset CSV
            sample_text = combined_headers_text + " " + " ".join([" ".join(r) for r in preview_rows])
            explicit_units = [f"{v[0]} {v[1]}" for v in self.numeric_unit_pattern.findall(sample_text)]
            all_numbers = self.generic_numeric_regex.findall(sample_text)
            semantic_metrics = self._compute_semantic_metrics(sample_text)
            
            return {
                "source": "Zenodo/Figshare Dataset (CSV Engine)",
                "title": f"Dataset Parameters: {filename}",
                "filename": filename,
                "variables_found": explicit_units,
                "semantic_metrics": semantic_metrics,
                "stats": {
                    "total_numbers": len(all_numbers),
                    "suspect_numbers": max(0, len(all_numbers) - len(explicit_units))
                },
                "csv_structure": {
                    "headers": header,
                    "analyzed_variables": analyzed_variables,
                    "preview_rows_count": len(preview_rows)
                }
            }
            
        except Exception:
            # Fallback definitivo: lettura come testo grezzo puro se la struttura tabellare fallisce
            explicit_units = [f"{v[0]} {v[1]}" for v in self.numeric_unit_pattern.findall(full_body_content)]
            all_numbers = self.generic_numeric_regex.findall(full_body_content)
            semantic_metrics = self._compute_semantic_metrics(full_body_content)
            
            return {
                "source": "Unstructured Flat File",
                "title": f"Raw Text Audit: {filename}",
                "filename": filename,
                "variables_found": explicit_units,
                "semantic_metrics": semantic_metrics,
                "stats": {
                    "total_numbers": len(all_numbers),
                    "suspect_numbers": max(0, len(all_numbers) - len(explicit_units))
                },
                "raw_text_preview": full_body_content[:400] + "..."
            }

    def analyze_file(self, filename):
        """Smista dinamicamente l'analisi in base all'estensione del file sorgente."""
        path = os.path.join(self.source_dir, filename)
        
        if filename.endswith(".html"):
            data = self.process_html(path, filename)
        elif filename.endswith((".csv", ".txt")):
            data = self.process_csv_txt(path, filename)
        else:
            return None
            
        # Salvataggio del JSON normalizzato standardizzato in data/extracted/
        output_filename = filename.rsplit('.', 1)[0] + ".json"
        with open(os.path.join(self.output_dir, output_filename), "w", encoding="utf-8") as out_f:
            json.dump(data, out_f, indent=2, ensure_ascii=False)
            
        return data