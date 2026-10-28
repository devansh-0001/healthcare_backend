from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import User
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.mappings.models import PatientDoctorMapping


class Command(BaseCommand):
    help = 'Seeds initial demonstration data for Synora Healthcare Backend'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting Synora data seeding...'))

        with transaction.atomic():
            # Create Demo User
            user, created = User.objects.get_or_create(
                email='dev@example.com',
                defaults={
                    'name': 'Devansh',
                    'is_staff': True,
                }
            )
            if created:
                user.set_password('StrongPass#123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {user.email} (password: StrongPass#123)'))
            else:
                self.stdout.write(f'User {user.email} already exists.')

            # Create Demo Doctors
            doctors_data = [
                {
                    'name': 'Sarah Jenkins',
                    'specialization': 'Cardiology',
                    'email': 'sarah.jenkins@synora.clinic',
                    'phone': '+15551112233',
                    'experience_years': 15,
                    'hospital': 'Synora Heart Institute',
                    'is_available': True
                },
                {
                    'name': 'Alexander Hayes',
                    'specialization': 'Neurology',
                    'email': 'alexander.hayes@synora.clinic',
                    'phone': '+15552223344',
                    'experience_years': 12,
                    'hospital': 'Synora Neurological Center',
                    'is_available': True
                },
                {
                    'name': 'Maya Patel',
                    'specialization': 'Internal Medicine',
                    'email': 'maya.patel@synora.clinic',
                    'phone': '+15553334455',
                    'experience_years': 9,
                    'hospital': 'Synora Central Clinic',
                    'is_available': True
                },
                {
                    'name': 'Robert Chen',
                    'specialization': 'Orthopedics',
                    'email': 'robert.chen@synora.clinic',
                    'phone': '+15554445566',
                    'experience_years': 16,
                    'hospital': 'Synora Orthopedic Pavilion',
                    'is_available': True
                },
                {
                    'name': 'Emily Vance',
                    'specialization': 'Pediatrics',
                    'email': 'emily.vance@synora.clinic',
                    'phone': '+15555556677',
                    'experience_years': 11,
                    'hospital': 'Synora Childrens Health',
                    'is_available': True
                },
                {
                    'name': 'Liam Thorne',
                    'specialization': 'Dermatology',
                    'email': 'liam.thorne@synora.clinic',
                    'phone': '+15556667788',
                    'experience_years': 7,
                    'hospital': 'Synora Dermatology Suite',
                    'is_available': True
                },
            ]

            created_doctors = []
            for doc in doctors_data:
                doctor, doc_created = Doctor.objects.get_or_create(
                    email=doc['email'],
                    defaults={
                        'name': doc['name'],
                        'specialization': doc['specialization'],
                        'phone': doc['phone'],
                        'experience_years': doc['experience_years'],
                        'hospital': doc['hospital'],
                        'is_available': doc['is_available'],
                        'created_by': user
                    }
                )
                created_doctors.append(doctor)

            self.stdout.write(self.style.SUCCESS(f'Verified {len(created_doctors)} doctors.'))

            # Create Demo Patients
            patients_data = [
                {
                    'name': 'Eleanor Vance',
                    'age': 42,
                    'gender': 'female',
                    'phone': '+15551234567',
                    'address': '742 Evergreen Terrace, Springfield',
                    'medical_history': 'Stage 1 Hypertension, seasonal pollen allergies'
                },
                {
                    'name': 'Marcus Sterling',
                    'age': 58,
                    'gender': 'male',
                    'phone': '+15559876543',
                    'address': '124 Conch Street, Pacific Grove',
                    'medical_history': 'Type 2 Diabetes, mild exercise-induced asthma'
                },
                {
                    'name': 'Aria Montgomery',
                    'age': 27,
                    'gender': 'female',
                    'phone': '+15552468101',
                    'address': '31 Spooner Street, Quahog',
                    'medical_history': 'No chronic illnesses, annual checkup normal'
                }
            ]

            created_patients = []
            for pat in patients_data:
                patient, pat_created = Patient.objects.get_or_create(
                    name=pat['name'],
                    created_by=user,
                    defaults={
                        'age': pat['age'],
                        'gender': pat['gender'],
                        'phone': pat['phone'],
                        'address': pat['address'],
                        'medical_history': pat['medical_history']
                    }
                )
                created_patients.append(patient)

            self.stdout.write(self.style.SUCCESS(f'Verified {len(created_patients)} patients.'))

            # Create Sample Mappings
            if len(created_patients) >= 2 and len(created_doctors) >= 4:
                # Eleanor -> Dr. Sarah Jenkins (Cardiology), Dr. Maya Patel (Internal Medicine)
                PatientDoctorMapping.objects.get_or_create(
                    patient=created_patients[0],
                    doctor=created_doctors[0]
                )
                PatientDoctorMapping.objects.get_or_create(
                    patient=created_patients[0],
                    doctor=created_doctors[2]
                )
                # Marcus -> Dr. Robert Chen (Orthopedics)
                PatientDoctorMapping.objects.get_or_create(
                    patient=created_patients[1],
                    doctor=created_doctors[3]
                )
                self.stdout.write(self.style.SUCCESS('Verified sample patient-doctor mappings.'))

        self.stdout.write(self.style.SUCCESS('Successfully completed Synora data seeding!'))
