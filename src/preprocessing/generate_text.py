import random


# ---------------------------------------------------------------------------
# LEGITIMATE claim texts — specific, coherent, factual
# ---------------------------------------------------------------------------
LEGIT_ACCIDENT = [
    "On March 14th at approximately 3:45 PM, while I was driving north on Oak Street, a silver Toyota Camry ran a red light at the intersection of Oak and Main and struck my vehicle on the driver's side. Two witnesses, Mrs. Sarah Collins and Mr. James Reid, were present and have provided their contact details. The police report number is #2024-1234. My vehicle sustained damage to the left front door panel. I have attached photos and the tow truck receipt.",
    "At around 9:10 AM on a Tuesday morning, I was stationary at a red light when the vehicle behind me rear-ended my car. The driver admitted fault at the scene. Officer Williams filed report number R-88492. I was taken to Saint Mary's hospital for a neck examination and was discharged the same day with mild whiplash. Repair estimate from authorized dealer is $3,200.",
    "During heavy rainfall on the evening of February 8th, I lost traction on Highway 12 and my vehicle skidded into a guardrail. No other vehicles were involved. I immediately called 911 and the incident is documented under report number 20240208-543. The front bumper and hood were damaged. I have three repair quotes ranging from $2,800 to $3,500.",
]

LEGIT_THEFT = [
    "I parked my vehicle in the designated area at the downtown parking garage (Level 3, Space 42) on November 2nd at 8:00 AM. When I returned at 5:30 PM, the car was not there. I immediately contacted the parking garage management and called the police. Officer Martinez filed a theft report number TH-4453. I have provided my parking ticket and all vehicle documentation.",
    "My vehicle was stolen from outside my residence at 44 Elm Avenue between 11:00 PM and 6:30 AM. I noticed it missing when I came out for work. The police have assigned case number 2024-CR-7721 to the incident. My car had a GPS tracker; I have provided the last known location data to the authorities.",
]

LEGIT_DAMAGE = [
    "On January 19th, a large pine tree fell on my car during a storm. Three neighbors witnessed the incident and the property damage was documented by my homeowner's insurance adjuster as well. I have photos timestamped from right after the incident, and a certified arborist confirmed the tree fell due to storm damage and root decay.",
    "Severe flooding on July 22nd caused water to enter the interior and engine bay of my vehicle. I have attached weather reports confirming 8 inches of rainfall in the area, photos of the flooded street, and a report from the city's emergency management office confirming the flood event.",
]

# ---------------------------------------------------------------------------
# FRAUDULENT claim texts — vague, inconsistent, urgent, exaggerated
# ---------------------------------------------------------------------------
FRAUD_ACCIDENT = [
    "The accident happened suddenly and I cannot clearly remember exactly what occurred. It was very fast and there were no witnesses around at the time. My car was seriously damaged, much more than it looks, and I need urgent processing of my maximum claim amount as I am in a very difficult financial situation right now. The other driver left before police arrived.",
    "I was just driving normally and then suddenly there was a crash. I am not sure exactly where it happened but it was somewhere near downtown area. There were no people around who saw it. I cannot provide exact time but it was during the day. The damages are very extensive and I wish to claim the full policy amount immediately as I have urgent bills.",
    "The incident happened last week, approximately. I cannot recall the exact details because I was in shock. No one witnessed it. The car is completely destroyed and the repair would cost more than buying a new one. I have been a loyal customer for years and I urgently need this claim approved as soon as possible.",
    "My vehicle was involved in an accident but I do not remember all the specifics. There were no witnesses and the police were not called. The damage is significant. I need this to be processed urgently. I have been trying to reach your office many times and I am very frustrated with the delays. Please process my full claim amount.",
]

FRAUD_THEFT = [
    "My car was stolen. I am not sure exactly when because I did not notice immediately. There were no cameras in the area and no witnesses. The police took the report but I think they will not find it. I would like to claim the full value as the car was in perfect condition before this. Please process this urgently as I have no way to get to work.",
    "The vehicle went missing. I parked it somewhere and when I came back it was gone. I cannot provide a precise time or exact location. I need the maximum insurance payout immediately. The car was recently serviced and was in excellent condition worth much more than the market value. I have been a customer for many years.",
]

FRAUD_DAMAGE = [
    "My car was severely damaged during the recent storms. The damage is total and I need immediate full compensation. The losses are huge and I cannot afford to wait. There is no specific report but the storm was very bad everyone knows that. I cannot provide photos right now but the damage is clearly visible to anyone who looks at it.",
    "The damage occurred due to natural causes. I am unable to provide exact documentation at this moment due to personal circumstances. The car is completely unusable and the value of the damage is much higher than the estimate. Please approve the full claim urgently as I am in financial distress.",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_claim_text(row) -> str:
    """Generate claim text that is correlated with the fraud label."""

    is_fraud = int(row.get('fraud_label', 0)) == 1
    incident = str(row.get('incident_type', ''))

    if is_fraud:
        if 'Theft' in incident or 'theft' in incident:
            return random.choice(FRAUD_THEFT)
        elif 'Collision' in incident or 'collision' in incident or 'Accident' in incident:
            return random.choice(FRAUD_ACCIDENT)
        else:
            return random.choice(FRAUD_DAMAGE + FRAUD_ACCIDENT)
    else:
        if 'Theft' in incident or 'theft' in incident:
            return random.choice(LEGIT_THEFT)
        elif 'Collision' in incident or 'collision' in incident or 'Accident' in incident:
            return random.choice(LEGIT_ACCIDENT)
        else:
            return random.choice(LEGIT_DAMAGE)


def add_claim_text(df):
    df['claim_text'] = df.apply(generate_claim_text, axis=1)
    return df