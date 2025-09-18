import os, json, time
from typing import Optional, Any, Dict, List
from supabase import create_client, Client
from parsers import extract_depth_from_text

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_ROLE = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))

sb: Client = create_client(SUPABASE_URL, SERVICE_ROLE)

def next_job() -> Optional[Dict[str, Any]]:
    r = sb.table("ingestion_jobs").select("*").eq("status","PENDING") \
        .order("created_at", desc=False).limit(BATCH_SIZE).execute()
    return r.data[0] if r.data else None

def update_job(job_id: int, **fields):
    fields["updated_at"] = "now()"
    sb.table("ingestion_jobs").update(fields).eq("id", job_id).execute()

def save_raw(job_id: int, payload: Dict[str, Any], confidence: float):
    sb.table("raw_extractions").insert({
        "job_id": job_id,
        "payload": json.dumps(payload),
        "confidence": confidence
    }).execute()

def call_admin_ingest(payload: Dict[str, Any]):
    # Direct insertion instead of using problematic database function
    try:
        # Clean zone code - preserve full zone identifier while creating safe database key
        zone_code = payload.get('zone_code', '')
        # Remove excessive whitespace but keep meaningful descriptors
        clean_zone_code = ' '.join(zone_code.split()).strip()
        
        if not clean_zone_code:
            raise Exception(f"Invalid zone_code: {zone_code}")
        
        # Create a safe database key by replacing problematic characters
        safe_zone_key = clean_zone_code.replace('\n', '_').replace(' ', '_').replace('<', 'lt').replace('>', 'gt').replace('+', 'plus').replace(',', '').replace('(', '').replace(')', '')
        
        # Insert/update zone
        zone_data = {
            'municipality_id': 1,
            'zone_code': clean_zone_code,  # Full descriptive zone code
            'zone_name': payload.get('zone_name', ''),
            'ordinance_url': payload.get('ordinance_url', ''),
            'effective_date': 'now()',
            'last_verified_at': 'now()',
            'is_current': True,
            'published': True,
            'zone_key': f"{payload.get('state', 'NJ')}_{payload.get('municipality', 'Unknown')}_{safe_zone_key}"
        }
        
        # Upsert zone
        zone_result = sb.table('zones').upsert(zone_data, on_conflict='municipality_id,zone_code').execute()
        zone_id = zone_result.data[0]['id']
        
        # Delete existing standards
        sb.table('standards').delete().eq('zone_id', zone_id).execute()
        
        # Map standards from JSONB to specific database columns
        all_standards = payload.get('all_standards', [])
        
        # Import acres conversion function
        from parsers import acres_to_sq_ft
        
        # Create mapping function to extract values from standards array with flexible key matching
        def get_standard_value(standards, target_key):
            # Define key mapping variations for better matching
            key_variations = {
                'area_interior_lots': ['area_interior_lots'],
                'frontage_interior_lots': ['frontage_interior_lots'],
                'area_corner_lots': ['area_corner_lots'],
                'frontage_corner_lots': ['frontage_corner_lots'],
                'buildable_lot_area': ['buildable_lot_area'],
                'front_yard_principal': ['front_yard_principal'],
                'side_yard_principal': ['side_yard_principal'],
                'street_side_yard_principal': ['street_side_yard_principal'],
                'rear_yard_principal': ['rear_yard_principal'],
                'street_rear_yard_principal': ['street_rear_yard_principal'],
                'front_yard_accessory': ['front_yard_accessory'],
                'side_yard_accessory': ['side_yard_accessory'],
                'street_side_yard_accessory': ['street_side_yard_accessory'],
                'rear_yard_accessory': ['rear_yard_accessory'],
                'street_rear_yard_accessory': ['street_rear_yard_accessory'],
                'max_building_coverage': ['max_building_coverage'],
                'max_lot_coverage': ['max_lot_coverage'],
                'stories_max_height': ['stories_max_height'],
                'feet_max_height': ['feet_max_height'],
                'total_min_gross_floor_area': ['total_min_gross_floor_area'],
                'first_floor_multistory_min_gross_floor_area': ['first_floor_multistory_min_gross_floor_area'],
                'max_gross_floor_area': ['max_gross_floor_area'],
                'maximum_far': ['maximum_far'],
                'maximum_density': ['maximum_density'],
                'depth_interior_lots': ['depth_interior_lots'],
                'depth_corner_lots': ['depth_corner_lots']
            }
            
            # Get all possible key variations for the target
            possible_keys = key_variations.get(target_key, [target_key])
            
            # Collect all valid values for this field (since there may be multiple)
            valid_values = []
            
            # Search for all matching key variations  
            for std in standards:
                std_key = std.get('key', '')
                if std_key in possible_keys:
                    value_numeric = std.get('value_numeric')
                    value_text = std.get('value_text', '')
                    unit = std.get('unit', '') or std.get('units', '')
                    
                    # Try numeric value first
                    if value_numeric is not None and value_numeric != 0:
                        # Convert acres to square feet for area fields
                        if unit == 'ac' and 'area' in target_key.lower():
                            value_numeric = acres_to_sq_ft(value_numeric)
                        valid_values.append(value_numeric)
                        continue
                    
                    # Try to convert text to float if it looks numeric
                    if value_text:
                        # Clean the text value
                        clean_text = str(value_text).strip().replace('%', '').replace(',', '')
                        
                        # Skip clearly invalid values
                        if clean_text.lower() in ['n/a', 'na', '—', '-', 'none', '', '(q)', '()', '0']:
                            continue
                            
                        # Check if it's a simple number
                        try:
                            val = float(clean_text)
                            if val > 0:  # Only accept positive values
                                # Convert acres to square feet for area fields if unit indicates acres
                                if unit == 'ac' and 'area' in target_key.lower():
                                    val = acres_to_sq_ft(val)
                                valid_values.append(val)
                                continue
                        except (ValueError, TypeError):
                            pass
                            
                        # Try extracting numbers from complex strings like '60% (B)', '20(a)', etc.
                        import re
                        numbers = re.findall(r'[\d.]+', clean_text)
                        if numbers:
                            try:
                                val = float(numbers[0])
                                if val > 0:  # Only accept positive values
                                    # Convert acres to square feet for area fields if unit indicates acres
                                    if unit == 'ac' and 'area' in target_key.lower():
                                        val = acres_to_sq_ft(val)
                                    valid_values.append(val)
                            except (ValueError, TypeError):
                                continue
            
            # Return the first valid value (or handle multiple values intelligently)
            if valid_values:
                # Remove duplicates first
                unique_values = list(dict.fromkeys(valid_values))  # Preserves order, removes duplicates
                
                # For area/frontage fields, take the first (usually main requirement)
                # For front yard, use max (less restrictive/primary requirement)
                # For side/rear yards, use min (most restrictive)
                # For coverage/density, take the first
                if 'front_yard' in target_key.lower():
                    return max(unique_values)  # Less restrictive front yard (primary requirement)
                elif any(keyword in target_key.lower() for keyword in ['side_yard', 'rear_yard', 'setback']):
                    return min(unique_values)  # Most restrictive setback for sides/rear
                else:
                    return unique_values[0]  # First/primary value
                    
            return None
        
        # Insert new standards with mapped fields
        # Get interior lot values first for potential fallback
        interior_area = get_standard_value(all_standards, 'area_interior_lots')
        interior_frontage = get_standard_value(all_standards, 'frontage_interior_lots')
        corner_area = get_standard_value(all_standards, 'area_corner_lots')
        corner_frontage = get_standard_value(all_standards, 'frontage_corner_lots')
        
        # Handle side yard extraction - check if we need to split street_side_yard values
        side_yard_principal = get_standard_value(all_standards, 'side_yard_principal')
        street_side_yard_principal = get_standard_value(all_standards, 'street_side_yard_principal')
        
        # Debug - confirm execution reaches this point for R-220
        if clean_zone_code == 'R-220':
            print(f"🔍 R-220 FLOW DEBUG: Reached side yard processing")
        
        # If side_yard is null but street_side_yard has data, check if we have multiple values to split
        if side_yard_principal is None and street_side_yard_principal is not None:
            # Get all street_side_yard_principal values
            street_side_values = []
            for std in all_standards:
                if std.get('key') == 'street_side_yard_principal' and std.get('value_numeric') is not None:
                    street_side_values.append(std.get('value_numeric'))
            
            # If we have exactly 2 values, assume smaller one is regular side yard, larger is street side
            if len(street_side_values) == 2:
                street_side_values = sorted(set(street_side_values))  # Remove duplicates and sort
                if len(street_side_values) == 2:
                    side_yard_principal = min(street_side_values)  # Smaller value = regular side yard
                    street_side_yard_principal = max(street_side_values)  # Larger value = street side yard
                    print(f"📐 Split side yard values for {clean_zone_code}: Side={side_yard_principal}, Street Side={street_side_yard_principal}")
                elif len(street_side_values) == 1:
                    # Only one unique value, keep as street side yard
                    street_side_yard_principal = street_side_values[0]
        
        # Handle rear yard extraction - check for multiple values mapped to street_rear_yard_principal
        if clean_zone_code == 'R-220':
            print(f"🔍 R-220 FLOW DEBUG: Starting rear yard processing")
            
        rear_yard_principal = get_standard_value(all_standards, 'rear_yard_principal')
        street_rear_yard_principal = get_standard_value(all_standards, 'street_rear_yard_principal')
        
        # Check if we have multiple street_rear_yard_principal values that need splitting
        street_rear_values = []
        for std in all_standards:
            if std.get('key') == 'street_rear_yard_principal' and std.get('value_numeric') is not None:
                street_rear_values.append(std.get('value_numeric'))
        
        # Debug rear yard processing for R-220
        if clean_zone_code == 'R-220':
            print(f"🔍 REAR DEBUG R-220: rear_yard_principal={rear_yard_principal}")
            print(f"🔍 REAR DEBUG R-220: street_rear_yard_principal={street_rear_yard_principal}")
            print(f"🔍 REAR DEBUG R-220: street_rear_values={street_rear_values}")
            print(f"🔍 REAR DEBUG R-220: condition: len >= 2? {len(street_rear_values) >= 2}, rear is None? {rear_yard_principal is None}")
            
        # If we have multiple values and no separate rear_yard_principal, split them
        if len(street_rear_values) >= 2 and rear_yard_principal is None:
            unique_values = sorted(set(street_rear_values))  # Remove duplicates and sort
            if len(unique_values) == 2:
                rear_yard_principal = max(unique_values)  # Larger value = regular rear yard
                street_rear_yard_principal = min(unique_values)  # Smaller value = street rear yard
                print(f"📐 Split rear yard values for {clean_zone_code}: Rear={rear_yard_principal}, Street Rear={street_rear_yard_principal}")
            elif len(unique_values) == 1:
                # All values are the same, keep as street rear yard
                street_rear_yard_principal = unique_values[0]
            else:
                # More than 2 unique values, take first and last
                rear_yard_principal = max(unique_values)
                street_rear_yard_principal = min(unique_values)
                print(f"📐 Split rear yard values for {clean_zone_code}: Rear={rear_yard_principal}, Street Rear={street_rear_yard_principal}")
        
        # Handle accessory building values - use principal building values as default
        # First try to get specific accessory building values
        front_yard_accessory = get_standard_value(all_standards, 'front_yard_accessory')
        side_yard_accessory = get_standard_value(all_standards, 'side_yard_accessory')
        street_side_yard_accessory = get_standard_value(all_standards, 'street_side_yard_accessory')
        rear_yard_accessory = get_standard_value(all_standards, 'rear_yard_accessory')
        street_rear_yard_accessory = get_standard_value(all_standards, 'street_rear_yard_accessory')
        
        # Apply same splitting logic to accessory building side yards
        # Debug for specific zones
        if clean_zone_code in ['R-45', 'R-22']:
            print(f"🔧 DEBUG {clean_zone_code}: side_yard_accessory={side_yard_accessory}, street_side_yard_accessory={street_side_yard_accessory}")
        
        # If side_yard_accessory is null but street_side_yard_accessory has data, check if we have multiple values to split
        if side_yard_accessory is None and street_side_yard_accessory is not None:
            # Get all street_side_yard_accessory values
            accessory_street_side_values = []
            for std in all_standards:
                if std.get('key') == 'street_side_yard_accessory' and std.get('value_numeric') is not None:
                    accessory_street_side_values.append(std.get('value_numeric'))
            
            unique_accessory_street_side_values = sorted(set(accessory_street_side_values))
            
            if len(unique_accessory_street_side_values) == 2:
                # Two distinct values - split them
                side_yard_accessory = min(unique_accessory_street_side_values)  # Smaller value = regular side yard
                street_side_yard_accessory = max(unique_accessory_street_side_values)  # Larger value = street side yard
                print(f"📐 Split accessory side yard values for {clean_zone_code}: Side={side_yard_accessory}, Street Side={street_side_yard_accessory}")
            elif len(unique_accessory_street_side_values) == 1:
                # Single value - this is likely a mislabeled regular side yard accessory
                side_yard_accessory = unique_accessory_street_side_values[0]
                # Keep the original street_side_yard_accessory value only if it's different from the moved value
                if street_side_yard_accessory == side_yard_accessory:
                    street_side_yard_accessory = None
                print(f"📐 Moved single accessory street side yard value to regular side yard for {clean_zone_code}: {side_yard_accessory}")
        
        # For front yard accessory, use more restrictive value (min) instead of principal logic (max)
        if front_yard_accessory is None:
            # Get all front_yard_principal values and use minimum for accessory buildings
            front_principal_values = []
            for std in all_standards:
                if std.get('key') == 'front_yard_principal' and std.get('value_numeric') is not None:
                    front_principal_values.append(std.get('value_numeric'))
            
            if front_principal_values:
                unique_front_values = sorted(set(front_principal_values))
                if len(unique_front_values) > 1:
                    # Use minimum value for accessory buildings (more restrictive)
                    front_yard_accessory = min(unique_front_values)
                    print(f"🏠 Using more restrictive front yard for accessory buildings in {clean_zone_code}: {front_yard_accessory} (vs principal: {max(unique_front_values)})")
                else:
                    # Only one value, use it
                    front_yard_accessory = unique_front_values[0]
            else:
                # Fallback to principal value if no front yard values found
                front_yard_accessory = get_standard_value(all_standards, 'front_yard_principal')
        if side_yard_accessory is None:
            side_yard_accessory = side_yard_principal
        if street_side_yard_accessory is None:
            street_side_yard_accessory = street_side_yard_principal
        if rear_yard_accessory is None:
            # For accessory buildings, use side yard value if available (more common uniform setback)
            # Otherwise fallback to rear yard principal
            if side_yard_accessory is not None:
                rear_yard_accessory = side_yard_accessory
                print(f"🏠 Using side yard accessory for rear yard accessory fallback in {clean_zone_code}: {rear_yard_accessory}")
            else:
                rear_yard_accessory = rear_yard_principal
        if street_rear_yard_accessory is None:
            street_rear_yard_accessory = street_rear_yard_principal
            
        # FINAL FALLBACK: If side_yard_accessory is still None but street_side_yard_accessory has value,
        # this means the value was mislabeled and should be moved to side_yard_accessory
        if clean_zone_code in ['R-45', 'R-22']:
            print(f"🔧 FINAL FALLBACK CHECK {clean_zone_code}: side_yard_accessory={side_yard_accessory}, street_side_yard_accessory={street_side_yard_accessory}, side_yard_principal={side_yard_principal}")
        
        if side_yard_accessory is None and street_side_yard_accessory is not None:
            # Check if both principals are also None - this indicates mislabeling
            if side_yard_principal is None:
                side_yard_accessory = street_side_yard_accessory
                print(f"📐 FINAL FALLBACK: Moved mislabeled street side yard accessory to regular side yard for {clean_zone_code}: {side_yard_accessory}")
                # Only clear street_side_yard_accessory if street_side_yard_principal is also None
                if street_side_yard_principal is None:
                    street_side_yard_accessory = None
                    
        # FINAL FALLBACK: Same logic for rear yard accessory buildings
        if clean_zone_code in ['R-45', 'R-22', 'R-90']:
            print(f"🔧 REAR FALLBACK CHECK {clean_zone_code}: rear_yard_accessory={rear_yard_accessory}, street_rear_yard_accessory={street_rear_yard_accessory}, rear_yard_principal={rear_yard_principal}")
        
        if rear_yard_accessory is None and street_rear_yard_accessory is not None:
            # Check if both principals are also None - this indicates mislabeling
            if rear_yard_principal is None:
                rear_yard_accessory = street_rear_yard_accessory
                print(f"📐 REAR FALLBACK: Moved mislabeled street rear yard accessory to regular rear yard for {clean_zone_code}: {rear_yard_accessory}")
                # Only clear street_rear_yard_accessory if street_rear_yard_principal is also None
                if street_rear_yard_principal is None:
                    street_rear_yard_accessory = None
        
        # Apply thousands conversion for area values that look like they need it
        # If corner lot area is small (< 1000) but interior is large (> 10000), apply same scaling
        if (corner_area is not None and interior_area is not None and 
            corner_area < 1000 and interior_area > 10000):
            scaling_factor = interior_area / corner_area if corner_area > 0 else 1000
            if 500 <= scaling_factor <= 2000:  # Reasonable scaling factor (e.g., 1000x)
                corner_area = corner_area * 1000
                print(f"📐 Applied 1000x scaling to corner lot area: {corner_area/1000} -> {corner_area}")
        
        # Fallback logic: if no corner lot data exists, use interior lot data
        if corner_area is None and interior_area is not None:
            corner_area = interior_area
            print(f"🔄 Using interior lot area as fallback for corner lots: {corner_area}")
            
        if corner_frontage is None and interior_frontage is not None:
            corner_frontage = interior_frontage
            print(f"🔄 Using interior lot frontage as fallback for corner lots: {corner_frontage}")
        
        # Extract depth measurements - first check for explicit depth standards
        depth_interior_lots = get_standard_value(all_standards, 'depth_interior_lots')
        depth_corner_lots = get_standard_value(all_standards, 'depth_corner_lots')
        
        print(f"📏 DEPTH DEBUG {clean_zone_code}: Found depth standards - interior: {depth_interior_lots}, corner: {depth_corner_lots}")
        print(f"📏 DEPTH DEBUG {clean_zone_code}: all_standards has {len(all_standards)} items:")
        for i, std in enumerate(all_standards):
            key = std.get('key', '')
            if 'depth' in key:
                print(f"  📏 DEPTH STANDARD {i}: {std}")
        print(f"📏 DEPTH DEBUG {clean_zone_code}: Looking for depth keys in get_standard_value function")
        
        # Fallback: Extract depth measurements from lot size text (legacy method)
        if depth_interior_lots is None:
            for std in all_standards:
                if std.get('key') == 'area_interior_lots' and std.get('value_text'):
                    extracted_depth = extract_depth_from_text(std.get('value_text'))
                    if extracted_depth:
                        depth_interior_lots = extracted_depth
                        print(f"📏 Fallback: Extracted interior lot depth for {clean_zone_code}: {depth_interior_lots} ft from '{std.get('value_text')}'")
                        break
        
        if depth_corner_lots is None:
            for std in all_standards:
                if std.get('key') == 'area_corner_lots' and std.get('value_text'):
                    extracted_depth = extract_depth_from_text(std.get('value_text'))
                    if extracted_depth:
                        depth_corner_lots = extracted_depth
                        print(f"📏 Fallback: Extracted corner lot depth for {clean_zone_code}: {depth_corner_lots} ft from '{std.get('value_text')}'")
                        break
        
        # If no corner lot depth found, use interior lot depth as fallback
        if depth_corner_lots is None and depth_interior_lots is not None:
            depth_corner_lots = depth_interior_lots
            print(f"🔄 Using interior lot depth as fallback for corner lots: {depth_corner_lots} ft")
        
        standards_data = {
            'zone_id': zone_id,
            'zone_code': clean_zone_code,
            'all_standards': all_standards,
            # Map to specific database columns
            'area_sqft_interior_lots': interior_area,
            'frontage_interior_lots': interior_frontage,
            'area_sqft_corner_lots': corner_area,
            'frontage_feet_corner_lots': corner_frontage,
            'buildable_lot_area': get_standard_value(all_standards, 'buildable_lot_area'),
            'front_yard_principal_building': get_standard_value(all_standards, 'front_yard_principal'),
            'side_yard_principal_building': side_yard_principal,
            'street_side_yard_principal_building': street_side_yard_principal,
            'rear_yard_principal_building': rear_yard_principal,
            'street_rear_yard_principal_building': street_rear_yard_principal,
            'front_yard_accessory_building': front_yard_accessory,
            'side_yard_accessory_building': side_yard_accessory,
            'street_side_yard_accessory_building': street_side_yard_accessory,
            'rear_yard_accessory_building': rear_yard_accessory,
            'street_rear_yard_accessory_building': street_rear_yard_accessory,
            'max_building_coverage_percent': get_standard_value(all_standards, 'max_building_coverage'),
            'max_lot_coverage_percent': get_standard_value(all_standards, 'max_lot_coverage'),
            'stories_max_height_principal_building': get_standard_value(all_standards, 'stories_max_height'),
            'feet_max_height_principal_building': get_standard_value(all_standards, 'feet_max_height'),
            'total_minimum_gross_floor_area': get_standard_value(all_standards, 'total_min_gross_floor_area'),
            'first_floor_multistory_min_gross_floor_area': get_standard_value(all_standards, 'first_floor_multistory_min_gross_floor_area'),
            'max_gross_floor_area': get_standard_value(all_standards, 'max_gross_floor_area'),
            'maximum_far': get_standard_value(all_standards, 'maximum_far'),
            'maximum_density': get_standard_value(all_standards, 'maximum_density'),
            # Depth measurements
            'depth_interior_lots_ft': depth_interior_lots,
            'depth_corner_lots_ft': depth_corner_lots
        }
        
        sb.table('standards').insert(standards_data).execute()
        
        print(f"✅ Successfully ingested zone: {clean_zone_code}")
        return True
        
    except Exception as e:
        print(f"❌ Direct ingestion failed for {payload.get('zone_code', 'unknown')}: {e}")
        raise e
