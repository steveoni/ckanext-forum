import pytest

from ckan.lib import search
from ckan.plugins import toolkit
from ckan.tests import helpers
from ckan.tests import factories

from ckanext.issues.tests import factories as issue_factories
from ckanext.issues.tests.fixtures import issues_setup, owner


@pytest.fixture
def org(owner):
    return factories.Organization(user=owner)

@pytest.fixture
def dataset(owner, org):
    return factories.Dataset(user=owner, owner_org=org['name'])

class TestCreateNewIssue(object):

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_create_new_issue(self, app, owner, org, dataset):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(
            url=toolkit.url_for('issues.new', dataset_id=dataset['id']),
            extra_environ=env,
        )
        print(dir(response))
        assert 200 == response._status_code
        data = {}
        data['title'] = 'new issue'
        data['description'] = 'test_description'
        response = app.post(
            url=toolkit.url_for('issues.new', dataset_id=dataset['id']),
            data={
                'title': 'new issue',
                'description': 'test_description'
            },
            extra_environ=env,
        )

        assert 200 == response._status_code
        assert 'Your issue has been registered, thank you for the feedback' in response

        issues = helpers.call_action('issue_search',
                                     dataset_id=dataset['id'])
        assert 1 == issues['count']
        assert 'new issue' == issues['results'][0]['title']
        assert 'test_description' == issues['results'][0]['description']


class TestCreateNewIssueComment(object):

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_create_new_comment(self, app, owner, org, dataset):
        issue = issue_factories.Issue(user=owner,
                                      user_id=owner['id'],
                                      dataset_id=dataset['id'])
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.post(
            url=toolkit.url_for('issues_comments',
                                issue_number=issue['number'],
                                dataset_id=dataset['id']),
            params={'comment': 'Comment'},
            extra_environ=env,
        )
        
        assert 200 == response._status_code
        issue_dict = toolkit.get_action('issue_show')(
            data_dict={
                'dataset_id': dataset['id'],
                'issue_number': issue['number'],
            }
        )
        assert 'Comment' == issue_dict['comments'][0]['comment']
