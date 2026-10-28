from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import User
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.mappings.models import PatientDoctorMapping


class MappingTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            name='User One',
            password='Password123#'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            name='User Two',
            password='Password123#'
        )

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

        # Create doctor
        self.doctor = Doctor.objects.create(
            name='Dr. Smith',
            specialization='Cardiology',
            email='smith@synora.com',
            phone='+12345678901',
            experience_years=10,
            hospital='Synora Clinic',
            created_by=self.user1
        )

        # Create patient for user1
        self.patient1 = Patient.objects.create(
            name='Patient One',
            age=30,
            gender='male',
            phone='+12345678902',
            address='Street 1',
            created_by=self.user1
        )

        # Create patient for user2
        self.patient2 = Patient.objects.create(
            name='Patient Two',
            age=40,
            gender='female',
            phone='+12345678903',
            address='Street 2',
            created_by=self.user2
        )

    def test_assign_doctor_to_patient_success(self):
        payload = {
            'patient': self.patient1.id,
            'doctor': self.doctor.id
        }
        response = self.client1.post('/api/mappings/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['patient_id'], self.patient1.id)
        self.assertEqual(response.data['doctor_id'], self.doctor.id)
        self.assertTrue(PatientDoctorMapping.objects.filter(patient=self.patient1, doctor=self.doctor).exists())

    def test_duplicate_doctor_assignment_rejected_400(self):
        payload = {
            'patient': self.patient1.id,
            'doctor': self.doctor.id
        }
        # First assignment
        self.client1.post('/api/mappings/', payload, format='json')

        # Duplicate assignment
        dup_response = self.client1.post('/api/mappings/', payload, format='json')
        self.assertEqual(dup_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', dup_response.data)
        self.assertEqual(dup_response.data['error']['code'], 'validation_error')

    def test_cannot_assign_to_other_users_patient_returns_404(self):
        # User 1 tries to assign doctor to User 2's patient
        payload = {
            'patient': self.patient2.id,
            'doctor': self.doctor.id
        }
        response = self.client1.post('/api/mappings/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_mappings_scoped_to_user_patients(self):
        # Assign doctor to patient 1
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor)

        # Assign doctor to patient 2
        PatientDoctorMapping.objects.create(patient=self.patient2, doctor=self.doctor)

        # User 1 lists mappings
        res1 = self.client1.get('/api/mappings/')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data['count'], 1)
        self.assertEqual(res1.data['results'][0]['patient_id'], self.patient1.id)

        # User 2 lists mappings
        res2 = self.client2.get('/api/mappings/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['count'], 1)
        self.assertEqual(res2.data['results'][0]['patient_id'], self.patient2.id)

    def test_get_patient_assigned_doctors(self):
        mapping = PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor)

        # User 1 views patient 1's care team
        res = self.client1.get(f'/api/mappings/{self.patient1.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['patient_id'], self.patient1.id)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['assigned_doctors'][0]['id'], mapping.id)

        # User 2 tries to view patient 1's care team -> 404
        cross_res = self.client2.get(f'/api/mappings/{self.patient1.id}/')
        self.assertEqual(cross_res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_mapping_removes_assignment_only(self):
        mapping = PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor)

        # User 2 tries to delete user 1's mapping -> 404
        forbidden_del = self.client2.delete(f'/api/mappings/{mapping.id}/')
        self.assertEqual(forbidden_del.status_code, status.HTTP_404_NOT_FOUND)

        # User 1 deletes mapping -> 204
        success_del = self.client1.delete(f'/api/mappings/{mapping.id}/')
        self.assertEqual(success_del.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PatientDoctorMapping.objects.filter(id=mapping.id).exists())

        # Patient and Doctor still exist
        self.assertTrue(Patient.objects.filter(id=self.patient1.id).exists())
        self.assertTrue(Doctor.objects.filter(id=self.doctor.id).exists())

    def test_deleting_patient_cascades_mappings(self):
        mapping = PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor)
        self.patient1.delete()
        self.assertFalse(PatientDoctorMapping.objects.filter(id=mapping.id).exists())
        self.assertTrue(Doctor.objects.filter(id=self.doctor.id).exists())
