import datetime

# Hardcoded approximate lat/lon for Delhi localities grounded in official safety vectors
RISK_ZONES = {
    "Sultanpuri": {"tier": "red", "lat": 28.6994, "lon": 77.0725},
    "Prem Nagar": {"tier": "red", "lat": 28.7022, "lon": 77.0428},
    "Nihal Vihar": {"tier": "red", "lat": 28.6655, "lon": 77.0652},
    "Anand Parbat": {"tier": "red", "lat": 28.6616, "lon": 77.1947},
    "ITO": {"tier": "red", "lat": 28.6284, "lon": 77.2410},
    "Jama Masjid": {"tier": "red", "lat": 28.6507, "lon": 77.2334},
    "Govindpuri": {"tier": "red", "lat": 28.5447, "lon": 77.2646},
    "Dwarka Mor": {"tier": "red", "lat": 28.6186, "lon": 77.0319},
    "Uttam Nagar": {"tier": "red", "lat": 28.6214, "lon": 77.0574},
    "Shadipur": {"tier": "red", "lat": 28.6517, "lon": 77.1581},
    "Chandni Chowk": {"tier": "red", "lat": 28.6560, "lon": 77.2307},
    "Kashmere Gate": {"tier": "red", "lat": 28.6675, "lon": 77.2291},
    "Dhaula Kuan": {"tier": "yellow", "lat": 28.5919, "lon": 77.1616},
    "Vasant Vihar": {"tier": "yellow", "lat": 28.5606, "lon": 77.1614},
    "Mehrauli": {"tier": "yellow", "lat": 28.5147, "lon": 77.1751},
    "Malviya Nagar": {"tier": "yellow", "lat": 28.5352, "lon": 77.2117},
    "Paharganj": {"tier": "yellow", "lat": 28.6438, "lon": 77.2144},
    "Karol Bagh": {"tier": "yellow", "lat": 28.6514, "lon": 77.1903},
    "Chanakyapuri": {"tier": "green", "lat": 28.5971, "lon": 77.1843},
    "Lutyens Delhi": {"tier": "green", "lat": 28.6128, "lon": 77.2295},
    "Connaught Place": {"tier": "green", "lat": 28.6304, "lon": 77.2177}
}

def calculate_risk(destination: str, hour: int, is_weekend: bool, active_stories_count: int = 0) -> dict:
    score = 0
    reasons = []
    
    # 1. Base Locality Factor Evaluation
    if destination in RISK_ZONES:
        tier = RISK_ZONES[destination]["tier"]
        if tier == "red":
            score += 40
            reasons.append("Flagged high-incident area by Delhi Police report (+40)")
        elif tier == "yellow":
            score += 20
            reasons.append("Moderate risk zone / high-footfall commercial area (+20)")
        elif tier == "green":
            score += 0
            reasons.append("Relatively lower reported incidents / highly patrolled zone (+0)")
    else:
        score += 15
        reasons.append("Unknown/Unclassified area - default caution profile (+15)")
        
    # 2. Night Hours Window (21:00 - 05:00)
    if hour >= 21 or hour < 5:
        score += 30
        reasons.append("Night travel window (21:00-05:00) (+30)")
        
    # 3. Critical Late-Night Window (23:00 - 04:00)
    if hour >= 23 or hour < 4:
        score += 10
        reasons.append("Critical late-night exposure frame (23:00-04:00) (+10)")
        
    # 4. Weekend Structural Variance
    if is_weekend and (hour >= 21 or hour < 5):
        score += 10
        reasons.append("Weekend night structural variance (+10)")
        
    # 5. Live Crowdsourced Modifier Matrix Integration
    if active_stories_count > 0:
        added_risk = active_stories_count * 15
        score += added_risk
        reasons.append(f"Active user-reported hazard flagged at this location (+{added_risk})")
        
    score = min(score, 100)
    
    if score <= 30:
        level = "Low"
    elif score <= 60:
        level = "Moderate"
    else:
        level = "High"
        
    return {"score": score, "level": level, "reasons": reasons}

