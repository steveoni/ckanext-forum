import pytest

from ckan.plugins import toolkit
from ckan.tests import helpers
from ckan.tests import factories

from ckanext.issues.tests import factories as issue_factories

from .fixtures import issues_setup

class TestIssuesShowController(object):

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_show_issue(self, app):
        user = factories.User()
        org = factories.Organization(user=user)
        dataset = factories.Dataset(user=user, owner_org=org['id'])

        issue = issue_factories.Issue(user=user,
                                      user_id=user['id'],
                                      dataset_id=dataset['id'])
        
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=toolkit.url_for('issues.show_issue',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
            extra_environ=env,
        )

        env = {'REMOTE_USER': user['name'].encode('ascii')}

        response = app.get(
            url=toolkit.url_for('issues.show_issue',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
            extra_environ=env,
        )
        assert issue['title'] in response
        assert issue['description'] in response
