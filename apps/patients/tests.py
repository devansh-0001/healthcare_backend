from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import User
from apps.patients.models import Patient


class PatientTests(TestCase):
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

        self.unauth_client = APIClient()

        self.patient_data = {
            'name': 'John Doe',
            'age': 35,
            'gender': 'male',
            'phone': '+12345678901',
            'address': '123 Main St, Springfield',
            'medical_history': 'Seasonal allergies'
        }

    def test_unauthenticated_access_returns_401(self):
        response = self.unauth_client.get('/api/patients/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error']['code'], 'not_authenticated')

    def test_create_patient_success(self):
        response = self.client1.post('/api/patients/', self.patient_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'John Doe')
        self.assertEqual(response.data['age'], 35)
        self.assertEqual(response.data['gender'], 'male')

        patient = Patient.objects.get(id=response.data['id'])
        self.assertEqual(patient.created_by, self.user1)

    def test_list_patients_only_returns_own_records(self):
        # User 1 creates a patient
        self.client1.post('/api/patients/', self.patient_data, format='json')

        # User 2 creates a patient
        patient2_data = self.patient_data.copy()
        patient2_data['name'] = 'Jane Doe'
        self.client2.post('/api/patients/', patient2_data, format='json')

        # User 1 lists patients
        response1 = self.client1.get('/api/patients/')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data['count'], 1)
        self.assertEqual(response1.data['results'][0]['name'], 'John Doe')

        # User 2 lists patients
        response2 = self.client2.get('/api/patients/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['count'], 1)
        self.assertEqual(response2.data['results'][0]['name'], 'Jane Doe')

    def test_access_other_users_patient_returns_404(self):
        create_res = self.client1.post('/api/patients/', self.patient_data, format='json')
        patient_id = create_res.data['id']

        # User 2 tries to GET patient 1's record
        response = self.client2.get(f'/api/patients/{patient_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error']['code'], 'not_found')

        # User 2 tries to PUT patient 1's record
        put_response = self.client2.put(f'/api/patients/{patient_id}/', self.patient_data, format='json')
        self.assertEqual(put_response.status_code, status.HTTP_404_NOT_FOUND)

        # User 2 tries to DELETE patient 1's record
        del_response = self.client2.delete(f'/api/patients/{patient_id}/')
        self.assertEqual(del_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_update_and_delete_patient(self):
        create_res = self.client1.post('/api/patients/', self.patient_data, format='json')
        patient_id = create_res.data['id']

        # Update
        updated_data = self.patient_data.copy()
        updated_data['name'] = 'Johnathan Doe'
        put_res = self.client1.put(f'/api/patients/{patient_id}/', updated_data, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)
        self.assertEqual(put_res.data['name'], 'Johnathan Doe')

        # Delete
        del_res = self.client1.delete(f'/api/patients/{patient_id}/')
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Patient.objects.filter(id=patient_id).exists())

    def test_validation_errors(self):
        # Invalid age (>120)
        invalid_data = self.patient_data.copy()
        invalid_data['age'] = 150
        res = self.client1.post('/api/patients/', invalid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid gender
        invalid_data = self.patient_data.copy()
        invalid_data['gender'] = 'alien'
        res = self.client1.post('/api/patients/', invalid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid phone (<10 digits)
        invalid_data = self.patient_data.copy()
        invalid_data['phone'] = '123'
        res = self.client1.post('/api/patients/', invalid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
