import re, unicodedata, yaml, os
from rapidfuzz import fuzz, process

# Canonical keys mapped to your specific database fields - EXPANDED for better coverage
CANON = {
  "zone": ["zone","district","zoning"],
  
  # Lot size fields - EXPANDED for better area recognition
  "area_interior_lots": [
    "minimum lot size interior lots area in square feet",
    "interior lots area in square feet", 
    "area square feet interior lots",
    "area interior", "interior lots area", "min lot area interior", "lot area interior",
    # Common PDF header variations
    "area sq ft interior lots", "area interior lots", "interior area", "lot area",
    "minimum area interior lots", "min area interior lots", "area square feet",
    "interior lots minimum area", "lot size area", "lot area interior",
    "min lot size area", "minimum lot area", "area requirements interior",
    "interior lots area requirements", "area interior lots sq ft",
    # Short forms commonly found in PDFs
    "area", "lot area", "min area", "minimum area", "sq ft", "square feet",
    "interior area", "area interior", "lot size", "minimum lot size",
    # Table header patterns
    "area in square feet", "area in sq ft", "lot area sq ft", 
    "minimum lot size area", "interior lot area", "interior lot size",
    "lot area minimum", "area minimum", "required area", "min required area",
    # Additional pattern variations
    "area sf", "area (sf)", "area - sf", "area sq.ft", "area (sq ft)",
    "lot area (sq ft)", "minimum lot area (sq ft)", "interior lots (sq ft)"
  ],
  "frontage_interior_lots": [
    "minimum lot size interior lots frontage feet",
    "interior lots frontage feet",
    "frontage interior lots", "frontage interior", "interior lots frontage", "width interior"
  ],
  "area_corner_lots": [
    "minimum lot size corner lots area square feet",
    "corner lots area square feet", 
    "area square feet corner lots", "area corner", "corner lots area", "lot area corner",
    # Expanded patterns for better corner lot detection
    "corner lots area in square feet", "corner lot area", "corner lot size",
    "minimum corner lot area", "corner lots minimum area", "area corner lots",
    "corner lot area square feet", "corner lots sq ft", "corner lots (sq ft)",
    "corner lot area (sq ft)", "minimum corner lot size", "corner lot requirements",
    "area requirements corner lots", "corner lot area requirements",
    # Common PDF variations
    "corner lots area", "area for corner lots", "corner lot minimum area",
    "corner lots minimum size", "corner lot size requirements"
  ],
  "frontage_corner_lots": [
    "minimum lot size corner lots frontage feet",
    "corner lots frontage feet",
    "frontage feet corner lots", "frontage corner", "corner lots frontage", "width corner",
    # Expanded patterns for better corner lot detection
    "corner lot frontage", "corner lots frontage in feet", "frontage corner lots",
    "minimum corner lot frontage", "corner lot width", "corner lots width",
    "frontage requirements corner lots", "corner lot frontage requirements",
    "corner lots frontage feet", "corner lot frontage (feet)",
    # Common PDF variations
    "frontage for corner lots", "corner lot minimum frontage",
    "corner lots minimum frontage", "corner lot frontage requirements"
  ],
  
  # Depth measurements (found within lot size columns)
  "depth_interior_lots": [
    "minimum lot size interior lots depth feet",
    "interior lots depth feet", 
    "depth interior lots", "depth interior", "interior depth", "interior lots depth",
    # Common variations for depth measurements
    "depth ft interior lots", "depth feet interior lots", "interior lot depth",
    "minimum depth interior lots", "depth minimum interior lots", 
    "lot depth interior", "interior lots minimum depth", "depth interior lots feet",
    # Additional patterns that might appear in PDFs
    "depth", "lot depth", "minimum depth", "depth feet", "depth ft"
  ],
  "depth_corner_lots": [
    "minimum lot size corner lots depth feet",
    "corner lots depth feet",
    "depth corner lots", "depth corner", "corner depth", "corner lots depth", 
    # Common variations for depth measurements
    "depth ft corner lots", "depth feet corner lots", "corner lot depth",
    "minimum depth corner lots", "depth minimum corner lots",
    "lot depth corner", "corner lots minimum depth", "depth corner lots feet",
    # Additional patterns that might appear in PDFs
    "corner depth feet", "corner lot minimum depth", "depth corner lot"
  ],
  
  # Other lot requirements
  "buildable_lot_area": ["buildable lot area", "buildable area"],
  
  # Yard setbacks - Principal Building
  "front_yard_principal": [
    "minimum required yard areas feet principal building front yard",
    "principal building front yard",
    "front yard principal building", "front yard principal", "front setback principal", "front yard"
  ],
  "side_yard_principal": [
    "minimum required yard areas feet principal building side yard", 
    "principal building side yard",
    "side yard principal building", "side yard principal", "side setback principal", "side yard each", "side yard"
  ],
  "street_side_yard_principal": [
    "minimum required yard areas feet principal building street side yard",
    "principal building street side yard", 
    "street side yard principal building", "street side yard principal", "street side setback principal", "street side yard"
  ],
  "rear_yard_principal": [
    "minimum required yard areas feet principal building rear yard",
    "principal building rear yard",
    "rear yard principal building", "rear yard principal", "rear setback principal", "rear yard"
  ],
  "street_rear_yard_principal": [
    "minimum required yard areas feet principal building street rear yard",
    "principal building street rear yard",
    "street rear yard principal building", "street rear yard principal", "street rear setback principal", "street rear yard"
  ],
  
  # Yard setbacks - Accessory Building
  "front_yard_accessory": [
    "minimum required yard areas feet accessory building front yard",
    "accessory building front yard",
    "front yard accessory building", "front yard accessory", "accessory front yard", "accessory front setback",
    # Direct PDF header matches
    "accessory building front", "front yard accessory", "accessory front"
  ],
  "side_yard_accessory": [
    "minimum required yard areas feet accessory building side yard",
    "accessory building side yard", 
    "side yard accessory building", "side yard accessory", "accessory side yard", "accessory side setback", "side yard*",
    # Direct PDF header matches
    "accessory building side", "side yard accessory", "accessory side"
  ],
  "street_side_yard_accessory": [
    "minimum required yard areas feet accessory building street side yard",
    "accessory building street side yard",
    "street side yard accessory building", "street side yard accessory", "accessory street side yard",
    # Direct PDF header matches
    "accessory building street side", "street side yard accessory", "accessory street side"
  ],
  "rear_yard_accessory": [
    "minimum required yard areas feet accessory building rear yard",
    "accessory building rear yard",
    "rear yard accessory building", "rear yard accessory", "accessory rear yard", "accessory rear setback", "rear yard*",
    # Direct PDF header matches
    "accessory building rear", "rear yard accessory", "accessory rear"
  ],
  "street_rear_yard_accessory": [
    "minimum required yard areas feet accessory building street rear yard", 
    "accessory building street rear yard",
    "street rear yard accessory building", "street rear yard accessory", "accessory street rear yard",
    # Direct PDF header matches
    "accessory building street rear", "street rear yard accessory", "accessory street rear"
  ],
  
  # Coverage and density
  "max_building_coverage": [
    "max building coverage",
    "maximum building coverage", "building coverage", "coverage by building", "max building coverage percent", "building coverage percent"
  ],
  "max_lot_coverage": [
    "max lot coverage", 
    "maximum lot coverage", "lot coverage", "lot coverage all improvements", "max lot coverage percent", "lot coverage percent"
  ],
  
  # Height restrictions
  "stories_max_height": [
    "max height prin building stories",
    "maximum height principal building stories",
    "stories max height principal building", "max height stories", "stories", "maximum stories"
  ],
  "feet_max_height": [
    "max height prin building feet", 
    "maximum height principal building feet",
    "feet max height principal building", "max height feet", "height feet", "maximum height feet", "ridge feet"
  ],
  
  # Floor area requirements  
  "total_min_gross_floor_area": [
    "minimum gross floor area square feet total",
    "minimum gross floor area total",
    "total minimum gross floor area", "minimum floor area total", "minimum floor area square feet", "total floor area"
  ],
  "first_floor_multistory_min_gross_floor_area": [
    "minimum gross floor area square feet first floor multistory",
    "minimum gross floor area first floor multistory", 
    "first floor multistory minimum gross floor area", "first floor minimum", "multistory first floor"
  ],
  "max_gross_floor_area": [
    "max gross floor area all structures square feet",
    "maximum gross floor area",
    "max gross floor area", "max gross floor area all structures", "maximum floor area",
    # New patterns to match the actual PDF headers with formatting
    "max gross floor area all structures square feet n",
    "max gross floor area all structures",
    "max gross floor area square feet",
    "gross floor area all structures",
    "gross floor area square feet",
    "max floor area all structures",
    "max gross floor area all structures square feet n",
    "maximum gross floor area all structures",
    "max gross floor area n"
  ],
  
  # Development standards
  "maximum_far": ["maximum far", "max far", "far", "floor area ratio"],
  "maximum_density": ["maximum density", "max density", "units per gross acre", "density", "dwelling units per acre"],
}

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii","ignore").decode()
    s = re.sub(r"\s+", " ", s).strip().lower()
    s = re.sub(r"\(.*?\)", "", s)  # drop units parentheticals to generalize
    return s

def load_profile(state: str, muni: str) -> dict:
    # profile filename pattern: "Municipality_State.yml"
    name = f"{muni.strip().replace(' ','_')}_{state.upper().strip()}.yml"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(script_dir, f"profiles/{name}"), "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        with open(os.path.join(script_dir, "profiles/default.yml"), "r") as f:
            return yaml.safe_load(f) or {}

def header_map(raw_headers: list[str], profile: dict) -> dict[str, str|None]:
    mapping: dict[str, str|None] = {}
    prof_aliases = profile.get("aliases", {})  # exact header -> canonical
    # prefer explicit profile map
    for h in raw_headers:
        hn = norm(h)
        if h in prof_aliases:
            mapping[h] = prof_aliases[h]; continue
        # fuzzy to CANON
        candidates = []
        for k, alts in CANON.items():
            for a in alts:
                score = fuzz.token_set_ratio(hn, norm(a)) / 100.0
                # Add specificity bonus - prefer patterns with more tokens/words
                pattern_tokens = len(norm(a).split())
                header_tokens = len(hn.split())
                specificity_bonus = min(pattern_tokens, header_tokens) * 0.01  # Small bonus for specificity
                adjusted_score = min(1.0, score + specificity_bonus)
                candidates.append((adjusted_score, k, a))
        
        if candidates:
            # Sort by score (desc), then by pattern specificity (prefer longer patterns)
            candidates.sort(key=lambda x: (x[0], len(x[2].split())), reverse=True)
            best_score, best_key, best_pattern = candidates[0]
        else:
            best_score, best_key, best_pattern = 0.0, None, ""
        
        # Use lower threshold for area fields to be more aggressive
        threshold = 0.55 if any("area" in alt.lower() for alt in CANON.get(best_key or "", [])) else float(profile.get("threshold", 0.72))
        mapping[h] = best_key if best_score >= threshold else None
        
        # Debug for corner/interior lots specifically
        if "corner" in hn or "interior" in hn:
            print(f"🔧 LOT DEBUG: Header '{h}' -> normalized '{hn}' -> mapped to '{mapping[h]}' (score: {best_score:.3f}, pattern: '{best_pattern}', threshold: {threshold:.3f})")
        
        # Debug for max gross floor area specifically
        if "gross" in hn and "floor" in hn and "area" in hn:
            print(f"🔧 MAX GROSS DEBUG: Header '{h}' -> normalized '{hn}' -> mapped to '{mapping[h]}' (score: {best_score:.3f}, threshold: {threshold:.3f})")
    return mapping
