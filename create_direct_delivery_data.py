#!/usr/bin/env python3
"""
Direct delivery data creator - bypasses complex breeding workflow
Creates minimal delivery records directly for testing puppy creation
"""

from app import app, db
from models import Dog, DogGender, DogStatus, PregnancyRecord, DeliveryRecord, PregnancyStatus
from datetime import datetime, date, timedelta

def create_direct_delivery_data():
    """Create delivery records directly without complex breeding workflow"""
    
    with app.app_context():
        print("Creating direct delivery test data...")
        
        # Check if we already have delivery records
        existing_deliveries = DeliveryRecord.query.count()
        if existing_deliveries > 0:
            print(f"Already have {existing_deliveries} delivery records")
            return
        
        # Get existing dogs or create simple ones
        female_dogs = Dog.query.filter(Dog.gender == DogGender.FEMALE).all()
        if not female_dogs:
            print("Creating sample female dog...")
            female1 = Dog()
            female1.name = "بيلا"
            female1.code = "F001"
            female1.breed = "جيرمن شيبرد"
            female1.gender = DogGender.FEMALE
            female1.birth_date = date(2020, 5, 15)
            female1.current_status = DogStatus.ACTIVE
            
            db.session.add(female1)
            db.session.commit()
            female_dogs = [female1]
            print(f"Created female dog: {female1.name}")
        
        # Create pregnancy records directly (without mating requirement)
        female = female_dogs[0]
        
        pregnancy = PregnancyRecord()
        pregnancy.dog_id = female.id
        pregnancy.mating_record_id = None  # Skip mating requirement for test data
        pregnancy.confirmed_date = date.today() - timedelta(days=42)
        pregnancy.expected_delivery_date = date.today() - timedelta(days=7)
        pregnancy.status = PregnancyStatus.DELIVERED
        pregnancy.notes = "حمل تجريبي لاختبار النظام"
        
        db.session.add(pregnancy)
        db.session.commit()
        print(f"Created pregnancy record for {female.name}")
        
        # Create delivery record
        delivery = DeliveryRecord()
        delivery.pregnancy_record_id = pregnancy.id
        delivery.delivery_date = pregnancy.expected_delivery_date
        delivery.total_puppies = 4
        delivery.live_births = 4
        delivery.stillbirths = 0
        delivery.mother_condition = "ممتازة"
        delivery.notes = "ولادة ناجحة - 4 جراء بصحة جيدة"
        
        db.session.add(delivery)
        db.session.commit()
        print(f"Created delivery record: {delivery.live_births} live puppies")
        
        # Create a second delivery for more test options
        pregnancy2 = PregnancyRecord()
        pregnancy2.dog_id = female.id
        pregnancy2.mating_record_id = None
        pregnancy2.confirmed_date = date.today() - timedelta(days=21)
        pregnancy2.expected_delivery_date = date.today() + timedelta(days=7)
        pregnancy2.status = PregnancyStatus.DELIVERED
        pregnancy2.notes = "حمل ثاني - بيانات تجريبية"
        
        db.session.add(pregnancy2)
        db.session.commit()
        
        delivery2 = DeliveryRecord()
        delivery2.pregnancy_record_id = pregnancy2.id
        delivery2.delivery_date = date.today() - timedelta(days=3)
        delivery2.total_puppies = 3
        delivery2.live_births = 3
        delivery2.stillbirths = 0
        delivery2.mother_condition = "جيدة"
        delivery2.notes = "ولادة ثانية - 3 جراء"
        
        db.session.add(delivery2)
        db.session.commit()
        print(f"Created second delivery record: {delivery2.live_births} live puppies")
        
        # Verify
        total_deliveries = DeliveryRecord.query.count()
        print(f"\nSuccess! Created {total_deliveries} delivery records")
        print("Puppy creation form should now show delivery records in dropdown!")

if __name__ == "__main__":
    create_direct_delivery_data()