import pytest
import bs4

from ckan.plugins import toolkit
from ckan.tests import helpers
from ckan.tests import factories

from ckanext.forums.tests import factories as issue_factories
from ckanext.forums.tests.fixtures import issues_setup, user, owner


@pytest.fixture
def org(owner):
    return factories.Organization(user=owner)

@pytest.fixture
def dataset(owner, org):
    return factories.Dataset(user=owner, owner_org=org['name'])

@pytest.fixture
def issue(owner, dataset):
    return issue_factories.Issue(user=owner,
                                user_id=owner['id'],
                                dataset_id=dataset['id'])



class TestIssuesController(object):

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_unauthorized_users_cannot_see_issues_on_a_dataset(self, app, owner, org, issue):
        '''test that a 401 is returned, previously this would just 500'''
        unauthorized_user = factories.User()

        env = {'REMOTE_USER': unauthorized_user['name'].encode('ascii')}
        dataset = factories.Dataset(user=owner, owner_org=org['name'],
                                                        private=True)
        response = app.get(
            url=toolkit.url_for('issues.show_issue',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
            extra_environ=env,
            expect_errors=True
        )
        assert response._status_code == 401


class TestIssuesControllerUpdate(object):
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_user_cannot_edit_another_users_issue(self, app, user,
                                                dataset, issue):

        env = {'REMOTE_USER': user['name'].encode('ascii')}

        response = app.post(toolkit.url_for('issues.edit',
                                            dataset_id=dataset['id'],
                                            issue_number=issue['number']),
            params={'title': 'edit', 'description': 'edited description'},
            extra_environ=env,
            expect_errors=True
        )
        assert response._status_code == 401


class TestShow(object):

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_not_found_issue_raises_404(self, app, owner, dataset):
        # issue_number changed from 'some nonsence' to 850
        # flask throws an error
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.show_issue',
                                            dataset_id=dataset['id'],
                                            issue_number=850),
            extra_environ=env,
            expect_errors=True,
        )
        assert response._status_code == 404

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_show_with_non_existing_package_404s(self, app, owner):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.show_issue',
                                            dataset_id='does not exist',
                                            issue_number=1),
            extra_environ=env,
            expect_errors=True,
        )
        assert response._status_code == 404


class TestDelete(object):
    @pytest.mark.usefixtures("clean_db", "issues_setup", "with_request_context")
    def test_delete(self, app, owner, dataset, issue):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}

        response = app  .post(toolkit.url_for('issues.delete',
                                            dataset_id=dataset['id'],
                                            issue_number=issue['number']),
            extra_environ=env,
        )
        # check we get redirected back to the issues overview page
        assert 200 == response._status_code
        # check the issue is now deleted.
        pytest.raises(toolkit.ObjectNotFound,
                      helpers.call_action,
                      'forum_show',
                      issue_number=issue['number'],
                      dataset_id=dataset['id'])

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_delete_unauthed_401s(self, app, user, dataset, issue):
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.post(toolkit.url_for('issues.delete',
                                            dataset_id=dataset['id'],
                                            issue_number=issue['number']),
            extra_environ=env,
            expect_errors=True
        )
        assert 401 == response._status_code

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_delete_button_appears_for_authed_user(self, app, owner, dataset, issue):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.show_issue',
                                            dataset_id=dataset['id'],
                                            issue_number=issue['number']),
            extra_environ=env,
        )

        form = bs4.BeautifulSoup(response.body)
        form = form.find('form', id='issue-comment-form')

        delete_link = form.find_all('a')[-1]
        # check the link of the delete
        assert 'Delete' == delete_link.text
        assert toolkit.url_for('issues.delete',
                            dataset_id=dataset['id'],
                            issue_number=issue['number']) ==\
                            delete_link.attrs['href']
        
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_delete_confirm_page(self, app, owner, dataset, issue):
        '''test the confirmation page renders and cancels correctly'''
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.delete',
                                            dataset_id=dataset['id'],
                                            issue_number=issue['number']),
            extra_environ=env,
        )
        form = bs4.BeautifulSoup(response.body)
        form = form.find('form', id='ckanext-issues-confirm-delete')
        
        # check the form target
        assert toolkit.url_for('issues.delete',
                            dataset_id=dataset['id'],
                            issue_number=issue['number']) ==\
                form.get('action')
            
        buttons = [i.text for i in form.find_all('button')]
        assert ['Cancel', 'Confirm Delete'] == buttons


    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_delete_button_not_present_for_unauthed_user(self, app,
                                                user, dataset, issue):
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.show_issue',
                                        dataset_id=dataset['id'],
                                        issue_number=issue['number']),
            extra_environ=env,
        )

        form = bs4.BeautifulSoup(response.body)
        form = form.find('form', id='issue-comment-form')

        assert 'Delete' not in form.text


class TestOrganization(object):
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_basic(self, app, owner, org, dataset, issue):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(
            url=toolkit.url_for('issues.issues_for_organization',
                                org_id=org['id']),
            extra_environ=env
        )
        soup = bs4.BeautifulSoup(response.body)
        issues = soup.find('section', {'class': 'issues-home'}).text
        assert '1 issue found' in issues
        issue_page = soup.find('div', {'id': 'issue-page'}).text
        assert dataset['title'] in issue_page
        assert issue['title'] in issue_page
        assert issue['description'] not in issue_page
