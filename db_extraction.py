import requests
import os
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import time

print("Starting data population from the VA Lighthouse API...")

API_KEY = "" 

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'resources.db')
Base = declarative_base()

class Resource(Base):
    __tablename__ = 'resource'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    website = Column(String(200))
    phone = Column(String(20))
    address = Column(String(200))

engine = create_engine(f'sqlite:///{db_path}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def fetch_and_populate(state, facility_type, category_name):
    """
    Fetches facilities for a specific STATE and type from the VA API.
    """
    api_url = "https://sandbox-api.va.gov/services/va_facilities/v1/facilities"
    page_number = 1
    has_more_pages = True
    total_facilities_for_state = 0

    while has_more_pages:
        params = {
            'state': state,
            'type': facility_type,
            'page': page_number,
            'per_page': 50
        }
        headers = {
            'apikey': API_KEY
        }

        time.sleep(0.5) 
        
        response = requests.get(api_url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            facilities = data.get('data', [])

            if not facilities:
                break

            for facility in facilities:
                total_facilities_for_state += 1
                attributes = facility.get('attributes', {})
                address = attributes.get('address', {}).get('physical', {})
                phone = attributes.get('phone', {}).get('main', 'N/A')
                full_address = f"{address.get('address_1', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip', '')}"
                
                new_resource = Resource(
                    name=attributes.get('name', 'N/A'),
                    category=category_name,
                    description=f"Facility Type: {attributes.get('classification', 'N/A')}",
                    website=attributes.get('website', ''),
                    phone=phone,
                    address=full_address.strip(', ')
                )
                session.add(new_resource)
            
            if 'next' in data.get('links', {}) and data['links']['next'] is not None:
                page_number += 1
            else:
                has_more_pages = False
        else:
            print(f"  !! Error for {state} [{category_name}]: Status {response.status_code}, Page {page_number}")
            break
            
    session.commit()
    print(f"  - Finished fetching {category_name} for {state}. Found {total_facilities_for_state} facilities.")

states = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

print("Clearing all old data from the database...")
session.query(Resource).delete()
session.commit()
print("Database cleared.")

for state_code in states:
    print(f"\n===== Processing State: {state_code} =====")
    fetch_and_populate(state=state_code, facility_type='health', category_name='Healthcare')
    fetch_and_populate(state=state_code, facility_type='benefits', category_name='Employment')
    fetch_and_populate(state=state_code, facility_type='cemetery', category_name='Housing') #keeping this category mapping for now
    fetch_and_populate(state=state_code, facility_type='vet_center', category_name='Mental Health')

session.close()

print("\nNATIONWIDE API data population complete! The 'resources.db' file is now updated with data for all 50 states.")
