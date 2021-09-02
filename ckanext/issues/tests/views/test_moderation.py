import pytest

from ckan.plugins import toolkit
from ckan.tests import helpers
from ckan.tests import factories

from ckanext.issues.tests import factories as issue_factories
from ckanext.issues.tests.fixtures import issues_setup, owner
from ckanext.issues import model


@pytest.fixture
def org(owner):
    return factories.Organization(user=owner)

@pytest.fixture
def dataset(owner, org):
    return factories.Dataset(user=owner,
                            owner_org=org['name'],
                            private=True)

@pytest.fixture
def issue(owner, dataset):
    return issue_factories.Issue(user=owner,
                                user_id=owner['id'],
                                dataset_id=dataset['id'])

class TestModeration(object):
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_moderate_all_organization_issues(self, app, owner, org, issue):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}

        issue = model.Issue.get(issue['id'])
        issue.visibility = 'hidden'
        issue.save()
        issue = vars(issue)

        response = app.get(toolkit.url_for(
                            'moderation.moderate_all_reported_issues',
                            organization_id=org['id']),
            extra_environ=env,
        )
        assert issue['title'] in response
        assert issue['description'] in response


class TestCommentModeration(object):
    @pytest.fixture
    def comment(self, issue, dataset):
        comment = issue_factories.IssueComment(
            dataset_id=dataset['id'],
            issue_number=issue['number'],
            comment='this is a comment',
        )
        return comment
    
    @pytest.fixture
    def comment2(self, issue, dataset):
        comment2 = issue_factories.IssueComment(
            dataset_id=dataset['id'],
            issue_number=issue['number'],
            comment='this should not be shown',
        )
        return comment2

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_moderate_all_organization_issues(self, app, owner, org, comment, comment2):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}

        comment = model.IssueComment.get(comment['id'])
        comment.visibility = 'hidden'
        comment.save()
        comment = vars(comment)

        response = app.get(toolkit.url_for(
                            'moderation.reported_comments',
                                organization_id=org['id']),
            extra_environ=env,
        )
        assert comment['comment'] in response
        assert comment2['comment'] not in response
