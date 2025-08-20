#!/usr/bin/env python3
"""
Comprehensive breeding system data seeder
Creates complete breeding workflow data: heat cycles -> mating -> pregnancy -> delivery -> puppies
"""

from app import app, db
from models import Dog, DogGender, DogStatus, HeatCycle, HeatStatus, MatingRecord, MatingResult, PregnancyRecord, PregnancyStatus, DeliveryRecord, PuppyRecord
from datetime import datetime, date, timedelta
import sys

def seed_breeding_system_data():
    """Create comprehensive breeding system sample data"""
    
    with app.app_context():
        print("🐕 Seeding comprehensive breeding system data...")
        
        # First ensure we have dogs
        female_dogs = Dog.query.filter(Dog.gender == DogGender.FEMALE).all()
        male_dogs = Dog.query.filter(Dog.gender == DogGender.MALE).all()
        
        if not female_dogs or not male_dogs:
            print("Creating breeding dogs...")
            
            # Create female dogs for breeding
            females_data = [
                {"name": "بيلا", "code": "F001", "breed": "جيرمن شيبرد", "birth_date": date(2020, 3, 15)},
                {"name": "لونا", "code": "F002", "breed": "لابرادور", "birth_date": date(2019, 8, 22)},
                {"name": "نوفا", "code": "F003", "breed": "روت وايلر", "birth_date": date(2021, 1, 10)},
            ]
            
            for female_data in females_data:
                if not Dog.query.filter_by(code=female_data["code"]).first():
                    female = Dog()
                    female.name = female_data["name"]
                    female.code = female_data["code"]
                    female.breed = female_data["breed"]
                    female.gender = DogGender.FEMALE
                    female.birth_date = female_data["birth_date"]
                    female.current_status = DogStatus.ACTIVE
                    female.weight = 25.5
                    female.height = 60.0
                    female.color = "بني وأسود"
                    female.markings = "علامات مميزة"
                    female.notes = "كلبة تربية ممتازة"
                    db.session.add(female)
                    print(f"  ✓ Created female: {female.name}")
            
            # Create male dogs for breeding
            males_data = [
                {"name": "ماكس", "code": "M001", "breed": "جيرمن شيبرد", "birth_date": date(2019, 5, 20)},
                {"name": "ريكس", "code": "M002", "breed": "لابرادور", "birth_date": date(2018, 11, 12)},
            ]
            
            for male_data in males_data:
                if not Dog.query.filter_by(code=male_data["code"]).first():
                    male = Dog()
                    male.name = male_data["name"]
                    male.code = male_data["code"]
                    male.breed = male_data["breed"]
                    male.gender = DogGender.MALE
                    male.birth_date = male_data["birth_date"]
                    male.current_status = DogStatus.ACTIVE
                    male.weight = 32.0
                    male.height = 65.0
                    male.color = "أسود وبني"
                    male.markings = "علامات مميزة"
                    male.notes = "ذكر تربية قوي"
                    db.session.add(male)
                    print(f"  ✓ Created male: {male.name}")
            
            db.session.commit()
            
            # Refresh lists
            female_dogs = Dog.query.filter(Dog.gender == DogGender.FEMALE).all()
            male_dogs = Dog.query.filter(Dog.gender == DogGender.MALE).all()
        
        print(f"Available dogs: {len(female_dogs)} females, {len(male_dogs)} males")
        
        # Create heat cycle records
        heat_cycles_created = 0
        for i, female in enumerate(female_dogs[:3]):  # Use first 3 females
            # Create multiple heat cycles for realistic data
            for cycle_num in range(1, 3):  # cycles 1 and 2
                start_date = date.today() - timedelta(days=120 - (cycle_num * 180))
                
                if not HeatCycle.query.filter_by(
                    dog_id=female.id, 
                    cycle_number=cycle_num
                ).first():
                    heat_cycle = HeatCycle()
                    heat_cycle.dog_id = female.id
                    heat_cycle.cycle_number = cycle_num
                    heat_cycle.start_date = start_date
                    heat_cycle.end_date = start_date + timedelta(days=14)
                    heat_cycle.duration_days = 14
                    heat_cycle.status = HeatStatus.COMPLETED
                    heat_cycle.behavioral_changes = "زيادة النشاط والاهتمام"
                    heat_cycle.physical_signs = "تورم وإفرازات طبيعية"
                    heat_cycle.appetite_changes = "طبيعية"
                    heat_cycle.notes = f"دورة شبق رقم {cycle_num} - طبيعية"
                    
                    db.session.add(heat_cycle)
                    heat_cycles_created += 1
        
        db.session.commit()
        print(f"  ✓ Created {heat_cycles_created} heat cycle records")
        
        # Create mating records
        matings_created = 0
        heat_cycles = HeatCycle.query.filter(HeatCycle.status == HeatStatus.COMPLETED).all()
        
        for i, heat_cycle in enumerate(heat_cycles[:4]):  # Create matings for first 4 heat cycles
            male = male_dogs[i % len(male_dogs)]  # Rotate through available males
            
            if not MatingRecord.query.filter_by(
                female_id=heat_cycle.dog_id,
                male_id=male.id,
                heat_cycle_id=heat_cycle.id
            ).first():
                mating = MatingRecord()
                mating.female_id = heat_cycle.dog_id
                mating.male_id = male.id
                mating.heat_cycle_id = heat_cycle.id
                mating.mating_date = heat_cycle.start_date + timedelta(days=7)
                mating.mating_time = datetime.strptime("10:30", "%H:%M").time()
                mating.location = "منطقة التزاوج المخصصة"
                mating.duration_minutes = 25
                mating.success_rate = 95
                mating.behavior_observed = "تزاوج طبيعي وناجح"
                mating.notes = f"تزاوج ناجح بين {heat_cycle.dog.name} و {male.name}"
                
                db.session.add(mating)
                matings_created += 1
        
        db.session.commit()
        print(f"  ✓ Created {matings_created} mating records")
        
        # Create pregnancy records
        pregnancies_created = 0
        successful_matings = MatingRecord.query.all()  # All matings are successful in our seed data
        
        for mating in successful_matings:
            if not PregnancyRecord.query.filter_by(mating_record_id=mating.id).first():
                pregnancy = PregnancyRecord()
                pregnancy.mating_record_id = mating.id
                pregnancy.dog_id = mating.female_id
                pregnancy.confirmed_date = mating.mating_date + timedelta(days=21)
                pregnancy.expected_delivery_date = mating.mating_date + timedelta(days=63)
                pregnancy.status = PregnancyStatus.DELIVERED
                
                # Add weekly checkups
                pregnancy.week_2_checkup = {
                    "date": (pregnancy.confirmed_date + timedelta(days=7)).isoformat(),
                    "weight": "26.2kg",
                    "condition": "ممتازة",
                    "notes": "علامات الحمل واضحة"
                }
                pregnancy.week_4_checkup = {
                    "date": (pregnancy.confirmed_date + timedelta(days=21)).isoformat(),
                    "weight": "27.8kg",
                    "condition": "جيدة جداً",
                    "notes": "نمو طبيعي للجنين"
                }
                pregnancy.week_6_checkup = {
                    "date": (pregnancy.confirmed_date + timedelta(days=35)).isoformat(),
                    "weight": "29.5kg",
                    "condition": "ممتازة",
                    "notes": "استعداد للولادة"
                }
                
                pregnancy.ultrasound_results = [
                    {
                        "date": (pregnancy.confirmed_date + timedelta(days=28)).isoformat(),
                        "findings": "4-5 أجنة بصحة جيدة",
                        "technician": "د. فاطمة الأشعة"
                    }
                ]
                
                pregnancy.special_diet = "غذاء عالي البروتين للحوامل"
                pregnancy.exercise_restrictions = "تمارين خفيفة، تجنب القفز"
                pregnancy.medications = [
                    {
                        "name": "فيتامينات ما قبل الولادة",
                        "dosage": "حبة واحدة يومياً",
                        "duration": "طوال فترة الحمل"
                    }
                ]
                pregnancy.notes = f"حمل طبيعي لـ {mating.female.name} من {mating.male.name}"
                
                db.session.add(pregnancy)
                pregnancies_created += 1
        
        db.session.commit()
        print(f"  ✓ Created {pregnancies_created} pregnancy records")
        
        # Create delivery records
        deliveries_created = 0
        completed_pregnancies = PregnancyRecord.query.filter(
            PregnancyRecord.status == PregnancyStatus.DELIVERED
        ).all()
        
        for pregnancy in completed_pregnancies:
            if not DeliveryRecord.query.filter_by(pregnancy_record_id=pregnancy.id).first():
                delivery = DeliveryRecord()
                delivery.pregnancy_record_id = pregnancy.id
                delivery.delivery_date = pregnancy.expected_delivery_date
                delivery.delivery_start_time = datetime.strptime("08:00", "%H:%M").time()
                delivery.delivery_end_time = datetime.strptime("12:30", "%H:%M").time()
                delivery.location = "غرفة الولادة المجهزة - قسم التربية"
                delivery.attendant_vet = "د. أحمد الطبيب البيطري"
                delivery.total_puppies = 4 + (deliveries_created % 3)  # 4-6 puppies
                delivery.live_births = delivery.total_puppies
                delivery.stillbirths = 0
                delivery.assistance_required = deliveries_created % 2 == 0  # Some need assistance
                delivery.delivery_complications = None if not delivery.assistance_required else "احتاجت مساعدة بسيطة"
                delivery.mother_condition = "ممتازة"
                delivery.notes = f"ولادة ناجحة لـ {pregnancy.dog.name} - {delivery.live_births} جراء أصحاء"
                
                db.session.add(delivery)
                deliveries_created += 1
        
        db.session.commit()
        print(f"  ✓ Created {deliveries_created} delivery records")
        
        # Create puppy records
        puppies_created = 0
        delivery_records = DeliveryRecord.query.all()
        
        for delivery in delivery_records:
            # Create puppies for each delivery
            for puppy_num in range(1, delivery.live_births + 1):
                if not PuppyRecord.query.filter_by(
                    delivery_record_id=delivery.id,
                    puppy_number=puppy_num
                ).first():
                    puppy = PuppyRecord()
                    puppy.delivery_record_id = delivery.id
                    puppy.puppy_number = puppy_num
                    puppy.name = f"جرو {puppy_num} - {delivery.pregnancy_record.dog.name[:3]}"
                    puppy.gender = DogGender.MALE if puppy_num % 2 == 1 else DogGender.FEMALE
                    puppy.birth_weight = 0.35 + (puppy_num * 0.05)  # 350-500g
                    puppy.birth_date = delivery.delivery_date
                    birth_hour = 9 + puppy_num if puppy_num < 6 else 9 + (puppy_num % 5)
                    puppy.birth_time = datetime.strptime(f"{birth_hour:02d}:15", "%H:%M").time()
                    puppy.birth_order = puppy_num
                    puppy.alive_at_birth = True
                    puppy.current_status = "صحي ونشط"
                    puppy.color = ["أسود", "بني", "ذهبي", "أبيض"][puppy_num % 4]
                    puppy.markings = f"علامات مميزة رقم {puppy_num}"
                    puppy.notes = f"جرو صحي - الرقم {puppy_num} في الولادة"
                    
                    db.session.add(puppy)
                    puppies_created += 1
        
        db.session.commit()
        print(f"  ✓ Created {puppies_created} puppy records")
        
        # Final verification
        print("\n📊 Breeding system data summary:")
        print(f"   • Heat cycles: {HeatCycle.query.count()}")
        print(f"   • Mating records: {MatingRecord.query.count()}")
        print(f"   • Pregnancy records: {PregnancyRecord.query.count()}")
        print(f"   • Delivery records: {DeliveryRecord.query.count()}")
        print(f"   • Puppy records: {PuppyRecord.query.count()}")
        print(f"   • Female dogs: {Dog.query.filter(Dog.gender == DogGender.FEMALE).count()}")
        print(f"   • Male dogs: {Dog.query.filter(Dog.gender == DogGender.MALE).count()}")
        
        print("\n✅ Complete breeding system data created successfully!")
        print("🐕 Puppy creation form should now have delivery records available!")

if __name__ == "__main__":
    seed_breeding_system_data()