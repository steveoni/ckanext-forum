import bs4
import pytest

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
    return issue_factories.Issue(user=owner, dataset_id=dataset['id'])

class TestIssueEdit(object):
# Tests edit function
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_edit_issue(self, app, owner, org, dataset, issue):
        # goto issue show page
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(
            url=toolkit.url_for('issues.show_issue',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
            extra_environ=env,
        )
        assert 200 == response._status_code
        response = app.post(
            url=toolkit.url_for('issues.edit',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
            params={
                'title': 'edited title',
                'description': 'edited description'
            },
            extra_environ=env,
        )
        result = helpers.call_action('forum_show',
                                      dataset_id=dataset['id'],
                                     issue_number=issue['number'])
        assert 'edited title' == result['title']
        assert 'edited description' == result['description']


class TestEditButton(object):
# Tests edit button in show.html
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_edit_button_appears_for_authorized_user(self, app, owner, org, dataset, issue):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}

        response = app.get(
            url=toolkit.url_for('issues.show_issue',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
            extra_environ=env,
        )

        soup = bs4.BeautifulSoup(response.body)
        edit_button = soup.find('div', {'id': 'issue-edit-button'})
        assert edit_button is not None

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_edit_button_does_not_appear_for_unauthorized_user(self, app, user,
                                                owner, dataset, org, issue):
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        response = app.get(
            url=toolkit.url_for('issues.show_issue',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
            extra_environ=env,
        )

        soup = bs4.BeautifulSoup(response.body)
        edit_button = soup.find('div', {'id': 'issue-edit-button'})
        assert edit_button is None
