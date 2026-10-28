from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import User
from apps.doctors.models import Doctor


class DoctorTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='dr.creator@example.com',
            name='Dr Creator User',
            password='Password123#'
        )
        self.user2 = User.objects.create_user(
            email='other.user@example.com',
            name='Other User',
            password='Password123#'
        )

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

        self.unauth_client = APIClient()

        self.doctor_data = {
            'name': 'Sarah Jenkins',
            'specialization': 'Cardiology',
            'email': 'sarah.jenkins@synora.com',
            'phone': '+19876543210',
            'experience_years': 12,
            'hospital': 'Synora Heart Institute',
            'is_available': True
        }

    def test_unauthenticated_access_returns_401(self):
        response = self.unauth_client.get('/api/doctors/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_doctor_success(self):
        response = self.client1.post('/api/doctors/', self.doctor_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Sarah Jenkins')
        self.assertEqual(response.data['created_by'], self.user1.id)

    def test_list_doctors_shared_across_users(self):
        self.client1.post('/api/doctors/', self.doctor_data, format='json')

        # User 2 can list doctors created by User 1
        response = self.client2.get('/api/doctors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Sarah Jenkins')

    def test_filter_and_search_doctors(self):
        self.client1.post('/api/doctors/', self.doctor_data, format='json')

        # Add second doctor
        doc2 = {
            'name': 'David Miller',
            'specialization': 'Neurology',
            'email': 'david.miller@synora.com',
            'phone': '+19876543211',
            'experience_years': 8,
            'hospital': 'Synora Brain Institute',
            'is_available': True
        }
        self.client1.post('/api/doctors/', doc2, format='json')

        # Filter by specialization
        res_filter = self.client2.get('/api/doctors/?specialization=cardiology')
        self.assertEqual(res_filter.status_code, status.HTTP_200_OK)
        self.assertEqual(res_filter.data['count'], 1)
        self.assertEqual(res_filter.data['results'][0]['specialization'], 'Cardiology')

        # Search by name
        res_search = self.client2.get('/api/doctors/?search=Miller')
        self.assertEqual(res_search.status_code, status.HTTP_200_OK)
        self.assertEqual(res_search.data['count'], 1)
        self.assertEqual(res_search.data['results'][0]['name'], 'David Miller')

    def test_update_permissions_creator_vs_non_creator(self):
        res = self.client1.post('/api/doctors/', self.doctor_data, format='json')
        doctor_id = res.data['id']

        # Non-creator (user2) attempts to update -> 403 Forbidden
        update_data = self.doctor_data.copy()
        update_data['name'] = 'Hacked Name'
        forbidden_res = self.client2.put(f'/api/doctors/{doctor_id}/', update_data, format='json')
        self.assertEqual(forbidden_res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(forbidden_res.data['error']['code'], 'permission_denied')

        # Creator updates -> 200 OK
        update_data['name'] = 'Dr. Sarah Jenkins MD'
        success_res = self.client1.put(f'/api/doctors/{doctor_id}/', update_data, format='json')
        self.assertEqual(success_res.status_code, status.HTTP_200_OK)
        self.assertEqual(success_res.data['name'], 'Dr. Sarah Jenkins MD')

    def test_delete_permissions_creator_vs_non_creator(self):
        res = self.client1.post('/api/doctors/', self.doctor_data, format='json')
        doctor_id = res.data['id']

        # Non-creator attempts to delete -> 403 Forbidden
        forbidden_del = self.client2.delete(f'/api/doctors/{doctor_id}/')
        self.assertEqual(forbidden_del.status_code, status.HTTP_403_FORBIDDEN)

        # Creator deletes -> 204 No Content
        success_del = self.client1.delete(f'/api/doctors/{doctor_id}/')
        self.assertEqual(success_del.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Doctor.objects.filter(id=doctor_id).exists())

    def test_duplicate_doctor_email_conflict(self):
        self.client1.post('/api/doctors/', self.doctor_data, format='json')
        dup_data = self.doctor_data.copy()
        dup_data['name'] = 'Another Doctor'
        response = self.client1.post('/api/doctors/', dup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
