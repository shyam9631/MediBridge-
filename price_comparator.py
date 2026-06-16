import requests
import json
import os

# ── Mock Medicine Database ────────────────────────────────────────────────
# Real APIs would require authentication, so using mock data for demo
MEDICINE_DATABASE = {
    'paracetamol': {
        'name': 'Paracetamol 500mg',
        'unit': 'Strip of 10 tablets',
        'platforms': {
            'PharmEasy': {'price': 45.50, 'discount': '10% off', 'delivery': 'Free - 2 hrs', 'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg': {'price': 42.00, 'discount': '15% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds': {'price': 48.75, 'discount': '5% off', 'delivery': 'Free - 4 hrs', 'in_stock': True, 'url': 'https://www.netmeds.com'}
        }
    },
    'metformin': {
        'name': 'Metformin 500mg',
        'unit': 'Strip of 15 tablets',
        'platforms': {
            'PharmEasy': {'price': 89.99, 'discount': '12% off', 'delivery': 'Free - 2 hrs', 'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg': {'price': 85.50, 'discount': '20% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds': {'price': 92.00, 'discount': '8% off', 'delivery': 'Free - 4 hrs', 'in_stock': False, 'url': 'https://www.netmeds.com'}
        }
    },
    'aspirin': {
        'name': 'Aspirin 75mg',
        'unit': 'Strip of 14 tablets',
        'platforms': {
            'PharmEasy': {'price': 35.00, 'discount': '5% off', 'delivery': 'Free - 2 hrs', 'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg': {'price': 32.50, 'discount': '18% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds': {'price': 37.50, 'discount': '3% off', 'delivery': 'Free - 4 hrs', 'in_stock': True, 'url': 'https://www.netmeds.com'}
        }
    },
    'omeprazole': {
        'name': 'Omeprazole 20mg',
        'unit': 'Strip of 10 capsules',
        'platforms': {
            'PharmEasy': {'price': 125.00, 'discount': '15% off', 'delivery': 'Free - 2 hrs', 'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg': {'price': 118.75, 'discount': '22% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds': {'price': 132.50, 'discount': '10% off', 'delivery': 'Free - 4 hrs', 'in_stock': True, 'url': 'https://www.netmeds.com'}
        }
    },
    'amlodipine': {
        'name': 'Amlodipine 5mg',
        'unit': 'Strip of 10 tablets',
        'platforms': {
            'PharmEasy': {'price': 65.99, 'discount': '8% off', 'delivery': 'Free - 2 hrs', 'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg': {'price': 62.25, 'discount': '16% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds': {'price': 68.50, 'discount': '6% off', 'delivery': 'Free - 4 hrs', 'in_stock': True, 'url': 'https://www.netmeds.com'}
        }
    },
    'lisinopril': {
        'name': 'Lisinopril 10mg',
        'unit': 'Strip of 10 tablets',
        'platforms': {
            'PharmEasy': {'price': 75.50, 'discount': '12% off', 'delivery': 'Free - 2 hrs', 'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg': {'price': 71.75, 'discount': '18% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds': {'price': 79.00, 'discount': '7% off', 'delivery': 'Free - 4 hrs', 'in_stock': False, 'url': 'https://www.netmeds.com'}
        }
    },
    'atorvastatin': {
        'name': 'Atorvastatin 20mg',
        'unit': 'Strip of 10 tablets',
        'platforms': {
            'PharmEasy': {'price': 95.75, 'discount': '10% off', 'delivery': 'Free - 2 hrs', 'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg': {'price': 89.99, 'discount': '20% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds': {'price': 102.50, 'discount': '5% off', 'delivery': 'Free - 4 hrs', 'in_stock': True, 'url': 'https://www.netmeds.com'}
        }
    },
    'ibuprofen': {
        'name': 'Ibuprofen 400mg',
        'unit': 'Strip of 15 tablets',
        'platforms': {
            'PharmEasy': {'price': 55.00, 'discount': '8% off', 'delivery': 'Free - 2 hrs', 'in_stock': True, 'url': 'https://www.pharmeasy.in'},
            '1mg': {'price': 51.50, 'discount': '14% off', 'delivery': 'Free - 30 mins', 'in_stock': True, 'url': 'https://www.1mg.com'},
            'Netmeds': {'price': 58.99, 'discount': '5% off', 'delivery': 'Free - 4 hrs', 'in_stock': True, 'url': 'https://www.netmeds.com'}
        }
    }
}

def search_medicine(medicine_name):
    """
    Search for a medicine by name and return price comparison data
    
    Args:
        medicine_name (str): Name of the medicine to search for
        
    Returns:
        dict: Comparison data with platforms, prices, and details
    """
    medicine_key = medicine_name.lower().strip()
    
    # Try exact match first
    if medicine_key in MEDICINE_DATABASE:
        data = MEDICINE_DATABASE[medicine_key]
        platforms = []
        
        for platform_name, details in data['platforms'].items():
            platforms.append({
                'name': platform_name,
                'price': details['price'],
                'discount': details.get('discount', ''),
                'delivery': details.get('delivery', ''),
                'in_stock': details.get('in_stock', True),
                'url': details.get('url', '#'),
                'is_cheapest': False
            })
        
        # Find cheapest
        cheapest_price = min(p['price'] for p in platforms)
        for p in platforms:
            p['is_cheapest'] = (p['price'] == cheapest_price)
        
        # Sort by price
        platforms.sort(key=lambda x: x['price'])
        
        return {
            'success': True,
            'medicine': data['name'],
            'unit': data['unit'],
            'platforms': platforms
        }
    
    # Partial match search
    for key, data in MEDICINE_DATABASE.items():
        if medicine_key in key or key in medicine_key:
            platforms = []
            
            for platform_name, details in data['platforms'].items():
                platforms.append({
                    'name': platform_name,
                    'price': details['price'],
                    'discount': details.get('discount', ''),
                    'delivery': details.get('delivery', ''),
                    'in_stock': details.get('in_stock', True),
                    'url': details.get('url', '#'),
                    'is_cheapest': False
                })
            
            # Find cheapest
            cheapest_price = min(p['price'] for p in platforms)
            for p in platforms:
                p['is_cheapest'] = (p['price'] == cheapest_price)
            
            # Sort by price
            platforms.sort(key=lambda x: x['price'])
            
            return {
                'success': True,
                'medicine': data['name'],
                'unit': data['unit'],
                'platforms': platforms
            }
    
    # Not found
    return {
        'success': False,
        'error': f'Medicine "{medicine_name}" not found in our database. Try: Paracetamol, Metformin, Aspirin, Omeprazole, or Amlodipine'
    }

def get_available_medicines():
    """Get list of all available medicines"""
    return list(MEDICINE_DATABASE.keys())
