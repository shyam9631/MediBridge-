import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Local Medicine Database ───────────────────────────────────────────────────
MEDICINE_DATABASE = {
    'paracetamol': {
        'name': 'Paracetamol 500mg',
        'unit': 'Strip of 10 tablets',
        'platforms': {
            'PharmEasy': {'price': 45.50, 'discount': '10% off', 'delivery': 'Free - 2 hrs',   'in_stock': True,  'url': 'https://www.pharmeasy.in'},
            '1mg':       {'price': 42.00, 'discount': '15% off', 'delivery': 'Free - 30 mins', 'in_stock': True,  'url': 'https://www.1mg.com'},
            'Netmeds':   {'price': 48.75, 'discount': '5% off',  'delivery': 'Free - 4 hrs',   'in_stock': True,  'url': 'https://www.netmeds.com'},
        }
    },
    'dolo': {
        'name': 'Dolo 650mg',
        'unit': 'Strip of 15 tablets',
        'platforms': {
            'PharmEasy': {'price': 30.00, 'discount': '5% off',  'delivery': 'Free - 2 hrs',   'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg':       {'price': 28.50, 'discount': '10% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds':   {'price': 32.00, 'discount': '3% off',  'delivery': 'Free - 4 hrs',   'in_stock': True, 'url': 'https://www.netmeds.com'},
        }
    },
    'metformin': {
        'name': 'Metformin 500mg',
        'unit': 'Strip of 15 tablets',
        'platforms': {
            'PharmEasy': {'price': 89.99, 'discount': '12% off', 'delivery': 'Free - 2 hrs',   'in_stock': True,  'url': 'https://www.pharmeasy.in'},
            '1mg':       {'price': 85.50, 'discount': '20% off', 'delivery': 'Free - 30 mins', 'in_stock': True,  'url': 'https://www.1mg.com'},
            'Netmeds':   {'price': 92.00, 'discount': '8% off',  'delivery': 'Free - 4 hrs',   'in_stock': False, 'url': 'https://www.netmeds.com'},
        }
    },
    'aspirin': {
        'name': 'Aspirin 75mg',
        'unit': 'Strip of 14 tablets',
        'platforms': {
            'PharmEasy': {'price': 35.00, 'discount': '5% off',  'delivery': 'Free - 2 hrs',   'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg':       {'price': 32.50, 'discount': '18% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds':   {'price': 37.50, 'discount': '3% off',  'delivery': 'Free - 4 hrs',   'in_stock': True, 'url': 'https://www.netmeds.com'},
        }
    },
    'azithromycin': {
        'name': 'Azithromycin 500mg',
        'unit': 'Strip of 3 tablets',
        'platforms': {
            'PharmEasy': {'price': 145.00, 'discount': '10% off', 'delivery': 'Free - 2 hrs',   'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg':       {'price': 138.50, 'discount': '18% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds':   {'price': 152.75, 'discount': '5% off',  'delivery': 'Free - 4 hrs',   'in_stock': True, 'url': 'https://www.netmeds.com'},
        }
    },
    'cetirizine': {
        'name': 'Cetirizine 10mg',
        'unit': 'Strip of 10 tablets',
        'platforms': {
            'PharmEasy': {'price': 28.50, 'discount': '12% off', 'delivery': 'Free - 2 hrs',   'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg':       {'price': 25.99, 'discount': '20% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds':   {'price': 31.00, 'discount': '5% off',  'delivery': 'Free - 4 hrs',   'in_stock': True, 'url': 'https://www.netmeds.com'},
        }
    },
    'omeprazole': {
        'name': 'Omeprazole 20mg',
        'unit': 'Strip of 10 capsules',
        'platforms': {
            'PharmEasy': {'price': 125.00, 'discount': '15% off', 'delivery': 'Free - 2 hrs',   'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg':       {'price': 118.75, 'discount': '22% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds':   {'price': 132.50, 'discount': '10% off', 'delivery': 'Free - 4 hrs',   'in_stock': True, 'url': 'https://www.netmeds.com'},
        }
    },
    'pantoprazole': {
        'name': 'Pantoprazole 40mg',
        'unit': 'Strip of 10 tablets',
        'platforms': {
            'PharmEasy': {'price': 98.00,  'discount': '15% off', 'delivery': 'Free - 2 hrs',   'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg':       {'price': 91.50,  'discount': '22% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds':   {'price': 105.00, 'discount': '8% off',  'delivery': 'Free - 4 hrs',   'in_stock': True, 'url': 'https://www.netmeds.com'},
        }
    },
    'amlodipine': {
        'name': 'Amlodipine 5mg',
        'unit': 'Strip of 10 tablets',
        'platforms': {
            'PharmEasy': {'price': 65.99, 'discount': '8% off',  'delivery': 'Free - 2 hrs',   'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg':       {'price': 62.25, 'discount': '16% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds':   {'price': 68.50, 'discount': '6% off',  'delivery': 'Free - 4 hrs',   'in_stock': True, 'url': 'https://www.netmeds.com'},
        }
    },
    'atorvastatin': {
        'name': 'Atorvastatin 20mg',
        'unit': 'Strip of 10 tablets',
        'platforms': {
            'PharmEasy': {'price': 95.75,  'discount': '10% off', 'delivery': 'Free - 2 hrs',   'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg':       {'price': 89.99,  'discount': '20% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds':   {'price': 102.50, 'discount': '5% off',  'delivery': 'Free - 4 hrs',   'in_stock': True, 'url': 'https://www.netmeds.com'},
        }
    },
    'ibuprofen': {
        'name': 'Ibuprofen 400mg',
        'unit': 'Strip of 15 tablets',
        'platforms': {
            'PharmEasy': {'price': 55.00, 'discount': '8% off',  'delivery': 'Free - 2 hrs',   'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg':       {'price': 51.50, 'discount': '14% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds':   {'price': 58.99, 'discount': '5% off',  'delivery': 'Free - 4 hrs',   'in_stock': True, 'url': 'https://www.netmeds.com'},
        }
    },
    'lisinopril': {
        'name': 'Lisinopril 10mg',
        'unit': 'Strip of 10 tablets',
        'platforms': {
            'PharmEasy': {'price': 75.50, 'discount': '12% off', 'delivery': 'Free - 2 hrs',   'in_stock': True,  'url': 'https://www.pharmeasy.in'},
            '1mg':       {'price': 71.75, 'discount': '18% off', 'delivery': 'Free - 30 mins', 'in_stock': True,  'url': 'https://www.1mg.com'},
            'Netmeds':   {'price': 79.00, 'discount': '7% off',  'delivery': 'Free - 4 hrs',   'in_stock': False, 'url': 'https://www.netmeds.com'},
        }
    },
}


# ── AI Fallback for unknown medicines ─────────────────────────────────────────
def _ai_generate_prices(medicine_name):
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        prompt = f"""You are a pharmacy price database for India.
Generate realistic price comparison data for the medicine: "{medicine_name}"

Respond ONLY with valid JSON, no markdown, no backticks, no extra text:
{{
  "name": "Medicine Name with dosage",
  "unit": "Strip of X tablets/capsules",
  "platforms": {{
    "PharmEasy": {{"price": 0.00, "discount": "X% off", "delivery": "Free - 2 hrs", "in_stock": true, "url": "https://www.pharmeasy.in"}},
    "1mg":       {{"price": 0.00, "discount": "X% off", "delivery": "Free - 30 mins", "in_stock": true, "url": "https://www.1mg.com"}},
    "Netmeds":   {{"price": 0.00, "discount": "X% off", "delivery": "Free - 4 hrs", "in_stock": true, "url": "https://www.netmeds.com"}}
  }}
}}

Rules:
- Use realistic Indian rupee (INR) prices
- Prices should vary 5-15% across platforms
- 1mg is usually cheapest, Netmeds most expensive
- Discounts between 5% and 25%
- If medicine name is invalid or nonsensical: set all prices to 0 and in_stock to false
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3,
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if model adds them
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)
        return _build_result(data)

    except json.JSONDecodeError:
        return {'success': False, 'error': f'Could not get prices for "{medicine_name}". Please try again.'}
    except Exception:
        return {'success': False, 'error': f'AI lookup failed for "{medicine_name}". Please try again.'}


# ── Result Builder ────────────────────────────────────────────────────────────
def _build_result(data):
    platforms = []
    for platform_name, details in data['platforms'].items():
        platforms.append({
            'name':        platform_name,
            'price':       details['price'],
            'discount':    details.get('discount', ''),
            'delivery':    details.get('delivery', ''),
            'in_stock':    details.get('in_stock', True),
            'url':         details.get('url', '#'),
            'is_cheapest': False,
        })

    # Mark cheapest among in-stock only
    in_stock_platforms = [p for p in platforms if p['in_stock']]
    if in_stock_platforms:
        cheapest_price = min(p['price'] for p in in_stock_platforms)
        for p in platforms:
            p['is_cheapest'] = p['in_stock'] and (p['price'] == cheapest_price)

    # Sort: cheapest first, out-of-stock last
    platforms.sort(key=lambda x: (not x['in_stock'], x['price']))

    return {
        'success':   True,
        'medicine':  data['name'],
        'unit':      data.get('unit', ''),
        'platforms': platforms,
    }


# ── Main Search Function ──────────────────────────────────────────────────────
def search_medicine(medicine_name):
    key = medicine_name.lower().strip()

    # 1. Exact match in local DB
    if key in MEDICINE_DATABASE:
        return _build_result(MEDICINE_DATABASE[key])

    # 2. Partial match in local DB
    for db_key, data in MEDICINE_DATABASE.items():
        if db_key in key or key in db_key:
            return _build_result(data)

    # 3. Not found locally → ask Groq AI
    print(f"[AI Fallback] '{medicine_name}' not in local DB, asking Groq...")
    return _ai_generate_prices(medicine_name)


def get_available_medicines():
    return list(MEDICINE_DATABASE.keys())