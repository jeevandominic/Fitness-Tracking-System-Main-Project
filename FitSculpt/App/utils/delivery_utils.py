from math import radians, sin, cos, sqrt, atan2

def get_nearest_center(pincode):
    """Determine nearest delivery center based on pincode and district mapping"""
    pincode = int(pincode)
    
    # Define district pincode ranges
    DISTRICT_RANGES = {
        'Thiruvananthapuram': (695000, 695999),
        'Kollam': (691000, 691999),
        'Pathanamthitta': (689000, 689999),
        'Alappuzha': (688000, 688999),
        'Kottayam': (686000, 686999),
        'Idukki': (685000, 685999),
        'Ernakulam': (682000, 683999),
        'Thrissur': (680000, 681999),
        'Palakkad': (678000, 679999),
        'Malappuram': (676000, 677999),
        'Kozhikode': (673000, 673999),
        'Wayanad': (673100, 673699),
        'Kannur': (670000, 670999),
        'Kasaragod': (671000, 671999),
    }
    
    # Define nearest centers for each district
    NEAREST_CENTERS = {
        'Thiruvananthapuram': 'Thiruvananthapuram',
        'Kollam': 'Thiruvananthapuram',
        'Pathanamthitta': 'Alappuzha',
        'Alappuzha': 'Alappuzha',
        'Kottayam': 'Ernakulam',  # Changed to Ernakulam as it's closer
        'Idukki': 'Ernakulam',
        'Ernakulam': 'Ernakulam',
        'Thrissur': 'Thrissur',
        'Palakkad': 'Thrissur',
        'Malappuram': 'Kozhikode',
        'Kozhikode': 'Kozhikode',
        'Wayanad': 'Kozhikode',
        'Kannur': 'Kozhikode',
        'Kasaragod': 'Kozhikode',
    }
    
    # Find the district based on pincode
    district = None
    for dist, (start, end) in DISTRICT_RANGES.items():
        if start <= pincode <= end:
            district = dist
            break
    
    # If district found, return its nearest center
    if district:
        return NEAREST_CENTERS[district]
    
    # If pincode not found in ranges, calculate nearest based on geographical location
    if pincode < 685000:  # South Kerala
        return 'Thiruvananthapuram'
    elif 685000 <= pincode < 683000:  # Central Kerala
        return 'Ernakulam'
    elif 683000 <= pincode < 678000:  # North-Central Kerala
        return 'Thrissur'
    else:  # North Kerala
        return 'Kozhikode'

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points in meters using the Haversine formula
    """
    R = 6371000  # Earth's radius in meters

    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance 