from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


def client_for(user):
    token, _ = Token.objects.get_or_create(user=user)
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return c


class TrackerTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='password123')
        self.bob = User.objects.create_user('bob', password='password123')
        self.eve = User.objects.create_user('eve', password='password123')
        self.a = client_for(self.alice)
        self.b = client_for(self.bob)
        self.e = client_for(self.eve)
        r = self.a.post('/api/projects/', {'key': 'proj', 'name': 'Demo'})
        self.assertEqual(r.status_code, 201, r.data)
        self.a.post('/api/projects/PROJ/members/', {'username': 'bob'})

    def issue(self, **kw):
        data = {'title': 'T', **kw}
        r = self.a.post('/api/projects/PROJ/issues/', data)
        self.assertEqual(r.status_code, 201, r.data)
        return r.data

    def test_register_and_login(self):
        r = APIClient().post('/api/auth/register/', {'username': 'new', 'password': 'password123'})
        self.assertEqual(r.status_code, 201)
        self.assertIn('token', r.data)
        r = APIClient().post('/api/auth/login/', {'username': 'new', 'password': 'password123'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['token'], Token.objects.get(user__username='new').key)

    def test_unauthenticated_rejected(self):
        self.assertEqual(APIClient().get('/api/projects/').status_code, 401)

    def test_project_key_uppercased_and_validated(self):
        self.assertEqual(self.alice.owned_projects.first().key, 'PROJ')
        r = self.a.post('/api/projects/', {'key': 'A1', 'name': 'bad'})
        self.assertEqual(r.status_code, 400)

    def test_issue_keys_increment(self):
        self.assertEqual(self.issue()['key'], 'PROJ-1')
        self.assertEqual(self.issue()['key'], 'PROJ-2')

    def test_non_member_cannot_access(self):
        self.issue()
        self.assertEqual(self.e.get('/api/projects/PROJ/').status_code, 404)
        self.assertEqual(self.e.get('/api/projects/PROJ/issues/').status_code, 404)
        self.assertEqual(self.e.post('/api/projects/PROJ/issues/', {'title': 'x'}).status_code, 404)

    def test_only_owner_can_add_members(self):
        r = self.b.post('/api/projects/PROJ/members/', {'username': 'eve'})
        self.assertEqual(r.status_code, 403)

    def test_workflow_transitions(self):
        n = self.issue()['number']
        url = f'/api/projects/PROJ/issues/{n}/'
        self.assertEqual(self.a.patch(url, {'status': 'done'}).status_code, 400)
        self.assertEqual(self.a.patch(url, {'status': 'in_progress'}).status_code, 200)
        self.assertEqual(self.a.patch(url, {'status': 'done'}).status_code, 200)
        self.assertEqual(self.a.patch(url, {'status': 'todo'}).status_code, 400)

    def test_assignee_must_be_member(self):
        r = self.a.post('/api/projects/PROJ/issues/', {'title': 'x', 'assignee_id': self.eve.id})
        self.assertEqual(r.status_code, 400)
        r = self.a.post('/api/projects/PROJ/issues/', {'title': 'x', 'assignee_id': self.bob.id})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['assignee']['username'], 'bob')

    def test_comments_and_activity(self):
        n = self.issue()['number']
        base = f'/api/projects/PROJ/issues/{n}/'
        self.assertEqual(self.b.post(base + 'comments/', {'body': 'hi'}).status_code, 201)
        comments = self.a.get(base + 'comments/').data
        self.assertEqual([c['body'] for c in comments], ['hi'])
        self.assertEqual(comments[0]['author']['username'], 'bob')
        self.b.patch(base, {'status': 'in_progress', 'priority': 'high'})
        log = {(x['field'], x['old_value'], x['new_value']) for x in self.a.get(base + 'activity/').data}
        self.assertEqual(log, {('status', 'todo', 'in_progress'), ('priority', 'medium', 'high')})

    def test_filters_and_search(self):
        self.issue(title='Login bug', type='bug', priority='high')
        self.issue(title='Write docs', type='task', assignee_id=self.bob.id)
        get = lambda q: [i['title'] for i in self.a.get('/api/projects/PROJ/issues/' + q).data]
        self.assertEqual(get('?type=bug'), ['Login bug'])
        self.assertEqual(get('?assignee=bob'), ['Write docs'])
        self.assertEqual(get('?q=docs'), ['Write docs'])
        self.assertEqual(get('?priority=high&type=task'), [])

    def test_delete_issue(self):
        n = self.issue()['number']
        self.assertEqual(self.a.delete(f'/api/projects/PROJ/issues/{n}/').status_code, 204)
        self.assertEqual(self.a.get(f'/api/projects/PROJ/issues/{n}/').status_code, 404)

    def test_board_page_served(self):
        self.assertContains(APIClient().get('/'), 'Tracker MVP')
