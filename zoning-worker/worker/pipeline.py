import pandas as pd
import re
from typing import Dict, Any, List
from mapping import header_map, load_profile
from parsers import parse_cell, compute_confidence, extract_depth_from_text

def coerce_headers(df: pd.DataFrame) -> list[str]:
    # Handle complex multi-level headers by combining up to 3 rows with parent propagation
    headers = []
    
    # Get first 3 rows as potential headers
    header_rows = []
    for i in range(min(3, len(df))):
        row = df.iloc[i].fillna("").astype(str).tolist()
        header_rows.append(row)
    
    # Track parent headers for each column (for spanned cells)
    parents = [""] * len(header_rows[0])
    
    # Process rows from top to bottom
    for row_idx in range(len(header_rows)):
        current_row = header_rows[row_idx]
        current_parent = ""
        
        for col_idx in range(len(current_row)):
            cell = current_row[col_idx].strip()
            
            if cell and cell.lower() not in ['none', 'nan', '']:
                # If this cell appears to be a parent (spanned), set as current_parent
                # Simple heuristic: if next cell is empty or it's a category name
                if col_idx + 1 < len(current_row) and not current_row[col_idx + 1].strip():
                    current_parent = cell
                else:
                    current_parent = ""
                
                # Update parent for this column
                if current_parent:
                    parents[col_idx] = current_parent
                else:
                    # Combine with existing parent if any
                    if parents[col_idx]:
                        header_parts = [parents[col_idx], cell]
                    else:
                        header_parts = [cell]
                    combined = " ".join(header_parts).replace("\\n", " ").replace("  ", " ").strip()
                    headers.append(combined) if len(headers) <= col_idx else None
            else:
                # Empty cell: propagate parent if in a span
                if current_parent:
                    parents[col_idx] = current_parent
    
    # Second pass: build final headers using parents
    final_headers = []
    for col_idx in range(len(header_rows[0])):
        header_parts = []
        for row_idx in range(len(header_rows)):
            cell = header_rows[row_idx][col_idx].strip()
            if cell and cell.lower() not in ['none', 'nan', '']:
                header_parts.append(cell)
        
        if parents[col_idx]:
            header_parts.insert(0, parents[col_idx])
        
        if header_parts:
            combined_header = " ".join(header_parts).replace("\\n", " ").replace("  ", " ").strip()
        else:
            combined_header = f"Column_{col_idx}"
        
        final_headers.append(combined_header)
    
    print(f"🔍 Combined headers: {final_headers}")
    return final_headers

def dataframe_to_payloads(
    df: pd.DataFrame,
    ctx: Dict[str, Any]
) -> List[Dict[str, Any]]:
    df = df.copy()
    df = df.dropna(how="all", axis=0).dropna(how="all", axis=1)
    if df.empty: return []

    headers = coerce_headers(df)
    # Skip the first 3 rows used for headers
    df = df.iloc[3:].reset_index(drop=True)
    df.columns = headers

    profile = load_profile(ctx["state"], ctx["municipality"])
    hmap = header_map(list(df.columns), profile)

    # find zone column
    zone_col = next((c for c,k in hmap.items() if k=="zone"), df.columns[0])
    payloads: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        # Handle pandas Series properly for zone column
        if zone_col in row.index:
            zone_val = str(row[zone_col]).strip()
        else:
            zone_val = ""
        if not zone_val or zone_val.lower() in {"zone","district"}:
            continue
        
        # Skip rows that look like headers or invalid data  
        if any(header_word in zone_val.lower() for header_word in ["frontage", "yard", "side", "rear", "street", "stories", "feet", "total", "floor", "multistory"]):
            continue
        if zone_val.lower() in {"none", "nan", "null", ""} or len(zone_val) > 200:
            continue
        # Skip rows with only symbols or non-alphanumeric characters, but allow single letters like "I"
        if zone_val in {"□", "∆", "○", "◊", "■", "▲", "●", "♦"} or (len(zone_val) > 1 and not any(c.isalnum() for c in zone_val)):
            continue
        
        print(f"🔍 Processing zone: '{zone_val}'")

        payload = {
            "state": ctx["state"],
            "county": ctx["county"],
            "municipality": ctx["municipality"],
            "zone_code": zone_val,
            "zone_name": None,
            "ordinance_url": ctx.get("ordinance_url"),
            "standards": [],
            "permitted_uses": [],
            "conditional_uses": []
        }

        for raw_col, canon in hmap.items():
            if canon and canon != "zone":
                # Handle pandas Series properly
                if raw_col in row.index:
                    cell_value = row[raw_col]
                    if hasattr(cell_value, 'iloc'):
                        cell_value = cell_value.iloc[0] if len(cell_value) > 0 else ""
                else:
                    cell_value = ""
                # Special handling for maximum density - always store as text
                if canon == "maximum_density":
                    if str(cell_value).strip() and str(cell_value).strip().lower() not in {"—", "-", "--", "n/a", "na"}:
                        entry = {"key": canon, "units": None, "section_ref": None}
                        entry["value_text"] = str(cell_value).strip()
                        # Still extract footnote markers
                        notes = " ".join(re.findall(r"\(([A-Za-z∆□]+)\)", str(cell_value))) or None
                        if notes: entry["notes"] = notes
                    else:
                        continue
                else:
                    vnum, units, note, raw_text = parse_cell(cell_value)
                    if vnum is None and (raw_text.strip()=="" or raw_text.strip().lower() in {"—","-","n/a"}):
                        continue
                    entry = {"key": canon, "units": units, "section_ref": None}
                    if units == "range" or (vnum is None and raw_text):
                        entry["value_text"] = raw_text
                    elif vnum is not None:
                        entry["value_numeric"] = vnum
                    else:
                        entry["value_text"] = raw_text
                    if note: entry["notes"] = note
                payload["standards"].append(entry)

        # Extract depth measurements with positional awareness
        # First, try to extract from area columns (embedded depth info)
        for raw_col, canon in hmap.items():
            if canon in ["area_interior_lots", "area_corner_lots"]:
                if raw_col in row.index:
                    cell_value = row[raw_col]
                    if hasattr(cell_value, 'iloc'):
                        cell_value = cell_value.iloc[0] if len(cell_value) > 0 else ""
                    
                    depth_value = extract_depth_from_text(str(cell_value))
                    if depth_value:
                        depth_key = "depth_interior_lots" if canon == "area_interior_lots" else "depth_corner_lots"
                        depth_entry = {
                            "key": depth_key, 
                            "value_numeric": depth_value,
                            "units": "ft", 
                            "section_ref": None
                        }
                        payload["standards"].append(depth_entry)
                        print(f"📏 Extracted {depth_key}: {depth_value} ft from '{str(cell_value)[:50]}...'")

        # Second, use positional logic for separate depth columns
        # Find columns that contain "depth" text and determine if they're for interior or corner lots
        header_list = list(df.columns)
        depth_columns = [(i, col) for i, col in enumerate(header_list) if 'depth' in col.lower()]
        
        for col_idx, depth_col in depth_columns:
            if depth_col in row.index:
                cell_value = row[depth_col]
                if hasattr(cell_value, 'iloc'):
                    cell_value = cell_value.iloc[0] if len(cell_value) > 0 else ""
                
                # Check if this is a numeric depth value
                try:
                    depth_value = float(str(cell_value).strip().replace(",", ""))
                    
                    # Use positional logic to determine if this is interior or corner
                    # Look for area columns before this depth column
                    area_before_depth = None
                    for i in range(col_idx - 1, -1, -1):  # Look backwards
                        col = header_list[i]
                        col_lower = col.lower()
                        
                        # Enhanced text-based detection
                        if any(word in col_lower for word in ["corner", "corner lots"]):
                            if any(word in col_lower for word in ["area", "sq ft", "square feet"]):
                                area_before_depth = "corner"
                                break
                        elif any(word in col_lower for word in ["interior", "interior lots"]):
                            if any(word in col_lower for word in ["area", "sq ft", "square feet"]):
                                area_before_depth = "interior"
                                break
                        
                        # Then check mapping as fallback
                        elif hmap.get(col) == "area_corner_lots":
                            area_before_depth = "corner"
                            break
                        elif hmap.get(col) == "area_interior_lots":
                            area_before_depth = "interior"
                            break
                    
                    # Determine depth key based on position
                    if area_before_depth == "corner":
                        depth_key = "depth_corner_lots"
                    elif area_before_depth == "interior":
                        depth_key = "depth_interior_lots"
                    else:
                        # Improved default: check the header itself for keywords
                        header_lower = depth_col.lower()
                        if "corner" in header_lower:
                            depth_key = "depth_corner_lots"
                        elif "interior" in header_lower:
                            depth_key = "depth_interior_lots"
                        else:
                            depth_key = "depth_interior_lots"
                            print(f"🔍 DEPTH DEBUG: Defaulting to interior depth for column {col_idx} ('{depth_col}'), no area type detected")
                    
                    # Check if we already have this depth type from area extraction
                    existing_keys = [s.get("key") for s in payload["standards"]]
                    if depth_key not in existing_keys:
                        depth_entry = {
                            "key": depth_key,
                            "value_numeric": depth_value,
                            "units": "ft",
                            "section_ref": None
                        }
                        payload["standards"].append(depth_entry)
                        print(f"📏 Positional extract {depth_key}: {depth_value} ft (column {col_idx}, area_before: {area_before_depth})")
                    
                except (ValueError, TypeError):
                    # Not a numeric depth value, skip
                    pass

        payload["_confidence"] = compute_confidence(hmap, payload["standards"])
        payloads.append(payload)

    return payloads
