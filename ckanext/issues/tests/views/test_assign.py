from bs4 import BeautifulSoup
import pytest

from ckan.plugins import toolkit
from ckan.tests import helpers
from ckan.tests import factories

from ckanext.issues.tests import factories as issue_factories
from ckanext.issues.tests.fixtures import issues_setup, owner

class TestAssign(object):
    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)

    @pytest.fixture
    def dataset(self, owner, org):
        return factories.Dataset(user=owner, owner_org=org['id'])

    @pytest.fixture
    def issue(self, owner, dataset):
        return issue_factories.Issue(user=owner,
                                    user_id=owner['id'],
                                    dataset_id=dataset['id'])

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_user_self_assign(self, app, owner, dataset, issue):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.post(toolkit.url_for('issues.assign',
                                    dataset_id=dataset['id'],
                                    issue_number=issue['number']),
            params={'assignee': owner['name']},
            extra_environ=env,
        )
        soup = BeautifulSoup(response.body)
        assignee = soup.find(id='ckanext-issues-assignee').text.strip()
        assert owner['name'] == assignee

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_assign_an_editor_to_an_issue(self, app, org, dataset, issue):
        editor = factories.User()
        test = helpers.call_action('member_create',
                                id=org['id'],
                                object=editor['id'],
                                object_type='user',
                                capacity='editor'
        )

        env = {'REMOTE_USER': editor['name'].encode('ascii')}
        response = app.post(toolkit.url_for('issues.assign',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
            params={'assignee': editor['name']},
            extra_environ=env,
        )
        soup = BeautifulSoup(response.body)
        assignee = soup.find(id='ckanext-issues-assignee').text.strip()
        assert editor['name'] == assignee

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_standard_user_cannot_assign(self, app, dataset, issue):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.post(toolkit.url_for('issues.assign',
                            dataset_id=dataset['id'],
                            issue_number=issue['number']),
            params={'assignee': user['name']},
            extra_environ=env,
            expect_errors=True
        )

        assert 401 == response.status_code

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_cannot_assign_an_issue_that_does_not_exist(self, app, owner, dataset):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        #issue number changed from 'not an issue' to a random int
        #flask backend breaks
        response = app.post(toolkit.url_for('issues.assign',
                            dataset_id=dataset['id'],
                            issue_number='2987'),
            params={'assignee': owner['name']},
            extra_environ=env,
            expect_errors=True
        )

        assert 404 == response.status_code

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_assign_form_does_not_appear_for_unauthorized_user(self, app,
                                                            dataset, issue):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.show_issue',
                                        dataset_id=dataset['id'],
                                        issue_number=issue['number']),
            extra_environ=env,
        )
        
        soup = BeautifulSoup(response.body)
        form = soup.find('form', id='ckanext-issues-assign')
        assert form is None

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_assign_form_does_not_appear_for_anon_user(self, app, owner,
                                                        dataset, issue):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.show_issue',
                                            dataset_id=dataset['id'],
                                            issue_number=issue['number']),
        )
        soup = BeautifulSoup(response.body)
        form = soup.find('form', id='ckanext-issues-assign')
        assert form is None

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_cannot_assign_if_user_does_not_exist(self, app, owner,
                                                    dataset, issue):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.post(toolkit.url_for('issues.assign',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
            params={'assignee': 'not an user'},                
            extra_environ=env,
        )
        assert 'User not an user does not exist' in response

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_creator_cannot_assign_if_they_cannot_package_update(self,
                                                        app, dataset, issue):
        user = factories.User()
        print(user['name'])
        issue = issue_factories.Issue(user=user,
                                      user_id=user['id'],
                                      dataset_id=dataset['id'])
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.post(toolkit.url_for('issues.assign',
                            dataset_id=dataset['id'],
                            issue_number=issue['number']),
            params={'assignee': user['name']},
            extra_environ=env,
            expect_errors=True
        )

        assert 401 == response.status_code
