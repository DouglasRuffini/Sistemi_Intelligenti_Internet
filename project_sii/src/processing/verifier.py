import os
import json

class PipelineVerifier:
    def __init__(self, extracted_dir="data/extracted/"):
        self.extracted_dir = extracted_dir

    def generate_summary(self):
        files = [f for f in os.listdir(self.extracted_dir) if f.endswith(".json") and f != "summary.json"]
        if not files:
            return {"status": "No data available"}
            
        total_suspect = 0
        global_term_counts = {}
        file_densities = []
        
        for file in files:
            with open(os.path.join(self.extracted_dir, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                
            total_suspect += data["stats"]["suspect_numbers"]
            file_densities.append({
                "file": data["filename"],
                "n_numeric": data["stats"]["total_numbers"],
                "metrics": data["semantic_metrics"]
            })
            
            # Aggregazione dei conteggi semantici complessivi
            for cat, val in data["semantic_metrics"].items():
                global_term_counts[cat] = global_term_counts.get(cat, 0) + val
                
        summary = {
            "n_files": len(files),
            "n_suspect_values_global": total_suspect,
            "global_term_counts": global_term_counts,
            "top_dense_files": sorted(file_densities, key=lambda x: x["n_numeric"], reverse=True)[:5]
        }
        
        with open(os.path.join(self.extracted_dir, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
            
        return summary