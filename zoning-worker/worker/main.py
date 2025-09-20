import os, traceback
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv(override=True)

AUTO_INGEST = os.getenv("AUTO_INGEST","true").lower() == "true"
CONF_THRESH = float(os.getenv("CONFIDENCE_THRESHOLD","0.90"))

from supa import next_job, update_job, save_raw, call_admin_ingest
from extractors import download_pdf, extract_tables
from pipeline import dataframe_to_payloads

def ctx_from_job(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "state": job["state_code"],
        "county": job["county"],
        "municipality": job["municipality"],
        "ordinance_url": job["source_url"],
    }

def process_job(job: Dict[str, Any]):
    update_job(job["id"], status="PROCESSING", message=None)
    pdf_path = download_pdf(job["source_url"])
    dfs = extract_tables(pdf_path)
    if not dfs:
        update_job(job["id"], status="FAILED", message="No tables found"); return

    ctx = ctx_from_job(job)
    all_payloads = []
    best_conf = 0.0

    for df in dfs:
        payloads = dataframe_to_payloads(df, ctx)
        if not payloads: continue
        all_payloads.extend(payloads)
        best_conf = max(best_conf, max((p.get("_confidence",0.0) for p in payloads), default=0.0))

    if not all_payloads:
        update_job(job["id"], status="FAILED", message="Parsed 0 payloads"); return

    # Group payloads by zone_code to create consolidated zone records
    zone_groups = {}
    for p in all_payloads:
        zone_code = p["zone_code"]
        if zone_code not in zone_groups:
            zone_groups[zone_code] = {
                "state": p["state"],
                "county": p["county"], 
                "municipality": p["municipality"],
                "zone_code": zone_code,
                "zone_name": p.get("zone_name"),
                "ordinance_url": p.get("ordinance_url"),
                "all_standards": [],
                "_confidence": p.get("_confidence", 0.0)
            }
        # Merge standards from this payload
        zone_groups[zone_code]["all_standards"].extend(p.get("standards", []))
        # Keep the highest confidence for this zone
        zone_groups[zone_code]["_confidence"] = max(
            zone_groups[zone_code]["_confidence"], 
            p.get("_confidence", 0.0)
        )

    consolidated_payloads = list(zone_groups.values())

    # Save raw for review always  
    save_raw(job["id"], {"payloads": consolidated_payloads}, best_conf)

    # Ingest ALL zones found (remove confidence threshold filtering)
    if AUTO_INGEST and consolidated_payloads:
        ingested = 0
        failed = 0
        for p in consolidated_payloads:
            try:
                p.pop("_confidence", None)
                # Fix: Copy all_standards to standards for database ingestion (keep both keys)
                if "all_standards" in p:
                    p["standards"] = p["all_standards"]
                    # Debug: Check for depth standards
                    depth_standards = [s for s in p["standards"] if s.get("key", "").startswith("depth_")]
                    if depth_standards:
                        print(f"🔍 Zone {p.get('zone_code', 'unknown')} - sending {len(depth_standards)} depth standards to database")
                        for ds in depth_standards:
                            print(f"  📏 {ds.get('key')}: {ds.get('value_numeric')} {ds.get('units', '')}")
                call_admin_ingest(p)
                ingested += 1
            except Exception as e:
                print(f"❌ Failed to ingest zone {p.get('zone_code', 'unknown')}: {e}")
                failed += 1
        
        msg = f"Ingested {ingested}/{len(consolidated_payloads)} zones (failed: {failed}); best_conf={best_conf:.2f}"
        status = "DONE" if failed == 0 else "PARTIAL_SUCCESS" if ingested > 0 else "FAILED"
        update_job(job["id"], status=status, message=msg)
    else:
        update_job(job["id"], status="NEEDS_REVIEW",
                   message=f"Found {len(consolidated_payloads)} zones; best_conf={best_conf:.2f} (AUTO_INGEST disabled)")

def main():
    from supa import POLL_INTERVAL
    print(f"🚀 Zoning worker started, polling every {POLL_INTERVAL} seconds...")
    while True:
        try:
            job = next_job()
            if not job:
                print("📋 No pending jobs found, waiting...")
                import time; time.sleep(POLL_INTERVAL); continue
            print(f"📄 Processing job {job['id']}: {job['source_url']}")
            process_job(job)
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            print(f"❌ Error getting/processing job: {error_msg}")
            if 'job' in locals() and job:
                try:
                    update_job(job["id"], status="FAILED", message=f"{error_msg}\n{traceback.format_exc()[:1500]}")
                except:
                    pass  # Don't crash if we can't update the job
            import time; time.sleep(POLL_INTERVAL)  # Wait before retrying

if __name__ == "__main__":
    main()
