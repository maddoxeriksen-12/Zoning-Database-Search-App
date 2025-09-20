import re
from typing import Tuple, Any

REQUIRED = {"pb_front_yard_ft","pb_side_yard_ft","pb_rear_yard_ft","max_height_ft","max_lot_coverage_pct"}

def acres_to_sq_ft(acres: float) -> float:
    """Convert acres to square feet. 1 acre = 43,560 square feet"""
    return acres * 43560

def parse_cell(cell: Any) -> Tuple[float|None, str|None, str|None, str]:
    raw = str(cell or "").strip()
    raw_norm = re.sub(r"\s+", " ", raw)
    if raw in {"", "—", "-", "--", "n/a", "na", "N/A"}:
        return None, None, None, raw
    # footnote markers
    notes = " ".join(re.findall(r"\(([A-Za-z∆□]+)\)", raw)) or None
    # percent
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", raw)
    if m: return float(m.group(1)), "%", notes, raw_norm
    # acres
    m = re.search(r"(\d+(?:\.\d+)?)\s*ac", raw, flags=re.I)
    if m: return float(m.group(1)), "ac", notes, raw_norm
    # range (with comma support for thousands)
    m = re.search(r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)", raw_norm)
    if m: 
        # Remove commas before converting to float
        num_str = m.group(1).replace(",", "")
        return float(num_str), "range", notes, raw_norm
    # number (with comma support for thousands)
    m = re.search(r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)", raw_norm)
    if m: 
        # Remove commas before converting to float
        num_str = m.group(1).replace(",", "")
        return float(num_str), None, notes, raw_norm
    return None, None, notes, raw_norm

def extract_depth_from_text(text: str) -> float|None:
    """Extract depth measurements from lot size text.
    
    Common patterns:
    - "20,000 sq ft x 150 ft depth"
    - "20,000 x 150"
    - "Area: 20,000 sq ft, Depth: 150 ft"
    - "20,000 sf / 150 ft deep"
    """
    if not text:
        return None
        
    text = str(text).lower().strip()
    
    # Pattern 1: "number x number" (second number is depth)
    pattern1 = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\s*ft|sf|square\s*feet)?\s*x\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:ft|feet)?', text)
    if pattern1:
        depth_str = pattern1.group(2).replace(',', '')
        return float(depth_str)
    
    # Pattern 2: Explicit "depth: number"
    pattern2 = re.search(r'depth:?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:ft|feet)?', text)
    if pattern2:
        depth_str = pattern2.group(1).replace(',', '')
        return float(depth_str)
    
    # Pattern 3: "number ft deep" or "number feet deep"
    pattern3 = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:ft|feet)\s+deep', text)
    if pattern3:
        depth_str = pattern3.group(1).replace(',', '')
        return float(depth_str)
    
    # Pattern 4: "/" separator (area / depth)
    pattern4 = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\s*ft|sf|square\s*feet)?\s*/\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:ft|feet)', text)
    if pattern4:
        depth_str = pattern4.group(2).replace(',', '')
        return float(depth_str)
    
    return None

def compute_confidence(header_map: dict, standards: list[dict]) -> float:
    mapped = sum(1 for v in header_map.values() if v)
    total = max(1, len(header_map))
    header_cov = mapped / total
    req_cov = sum(1 for k in REQUIRED if any(s["key"]==k for s in standards)) / max(1, len(REQUIRED))
    parsable = sum(1 for s in standards if ("value_numeric" in s or "value_text" in s)) / max(1, len(standards))
    return 0.5*header_cov + 0.3*req_cov + 0.2*parsable
