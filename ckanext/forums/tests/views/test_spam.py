import pytest

from ckan import model
from ckan.plugins import toolkit
from ckan.tests import factories

from ckanext.forums.model import Issue, IssueComment, AbuseStatus
from ckanext.forums.tests import factories as issue_factories
from ckanext.forums.tests.fixtures import issues_setup, owner, user


class TestModeratedAbuseReport(object):
    @pytest.fixture
    def reporter(self):
        return factories.User()

    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)

    @pytest.fixture
    def dataset(self, owner, org):
        return factories.Dataset(user=owner, owner_org=org['name'])

    @pytest.fixture
    def issue_abuse(self, owner, dataset, reporter):
        issue_abuse1 = issue_factories.Issue(user=owner,
                                    user_id=owner['id'],
                                    dataset_id=dataset['id'])
        issue_abuse1 = Issue.get(issue_abuse1['id'])
        issue_abuse1.visibility = 'hidden'
        issue_abuse1.report_abuse(model.Session, reporter['id'])
        issue_abuse1.abuse_status = AbuseStatus.abuse.value
        issue_abuse1.save()
        return vars(issue_abuse1)

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_abuse_label_appears_for_admin(self, app, reporter, owner, dataset, issue_abuse):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.show_issue',
                                dataset_id=dataset['id'],
                                issue_number=issue_abuse['number']),
            extra_environ=env,
        )
        print('------------', response.body)

        assert 'Test Issue' in response.body
        assert 'Hidden from normal users' in response.body
        assert 'Moderated: 1' in response.body
        assert '1 user reports this is spam/abus' in response.body


    @pytest.mark.usefixtures("clean_db", "issues_setup", "issue_abuse")
    def test_reported_as_abuse_appears_in_search_as_admin(self, app, owner, dataset):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.dataset',
                                dataset_id=dataset['id']),
            extra_environ=env,
        )

        assert '1 issue found' in response.body
        assert 'Test Issue' in response.body
        assert 'Spam/Abuse - hidden from normal users' in response.body


    @pytest.mark.usefixtures("clean_db", "issues_setup", "issue_abuse")
    def test_reported_as_abuse_does_not_appear_in_search_to_user_who_reported_it(self, app, dataset, reporter):
        env = {'REMOTE_USER': reporter['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.dataset',
                                dataset_id=dataset['id']),
            extra_environ=env,
        )

        assert 'No issues found' in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup", "issue_abuse")
    def test_reported_as_abuse_does_not_appear_as_non_admin(self, app, user, dataset):
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.dataset',
                                dataset_id=dataset['id']),
            extra_environ=env,
        )
        print(response.body)

        assert 'No issues found' in response.body
        assert 'Spam' not in response.body


class TestUnmoderatedAbuseReport(object):
    @pytest.fixture
    def reporter(self):
        return factories.User()

    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)
    
    @pytest.fixture
    def dataset(self, owner, org):
        return factories.Dataset(user=owner, owner_org=org['name'])
        # issue_reported is reported by a user but not moderated - i.e. may be
        # abuse/spam but it is still visible
    @pytest.fixture
    def issue_reported(self, owner, reporter, dataset):
        issue_reported1 = issue_factories.Issue(
                                user=owner,
                                user_id=owner['id'],
                                dataset_id=dataset['id'])
        issue_reported1 = Issue.get(issue_reported1['id'])
        issue_reported1.visibility = 'visible'
        issue_reported1.report_abuse(model.Session, reporter['id'])
        issue_reported1.abuse_status = AbuseStatus.unmoderated.value
        issue_reported1.save()
        return vars(issue_reported1)

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_abuse_label_appears_for_admin(self, app, owner,
                                    dataset, issue_reported, reporter):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.show_issue',
                                dataset_id=dataset['id'],
                                issue_number=issue_reported['number']),
            extra_environ=env,
        )

        assert 'Test Issue' in response.body
        assert 'Hidden from normal users' not in response.body
        assert 'Moderated' not in response.body
        assert '1 user reports this is spam/abuse' in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup", "issue_reported")
    def test_reported_as_abuse_appears_in_search_as_admin(self, app, owner, dataset):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.dataset',
                                        dataset_id=dataset['id']),
            extra_environ=env,
        )

        assert '1 issue found' in response.body
        assert 'Test Issue' in response.body
        assert 'Spam/Abuse' not in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup", "issue_reported")
    def test_reported_as_abuse_appears_in_search_to_user_who_reported_it(self,
                                                        app, reporter, dataset):
        env = {'REMOTE_USER': reporter['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.dataset',
                                dataset_id=dataset['id']),
            extra_environ=env,
        )

        assert '1 issue found' in response.body
        assert 'Test Issue' in response.body
        assert 'Reported by you to admins' in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup", "issue_reported")
    def test_reported_as_abuse_appears_as_non_admin(self, app, user, dataset):
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.dataset',
                                dataset_id=dataset['id']),
            extra_environ=env,
        )

        assert '1 issue found' in response.body
        assert 'Test Issue' in response.body
        assert 'Spam' not in response.body


class TestReportIssue(object):
    @pytest.fixture
    def joe_public(self):
        return factories.User()

    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)

    @pytest.fixture
    def dataset(self, owner, org):
        return factories.Dataset(user=owner, owner_org=org['name'])

    @pytest.fixture
    def issue(self, owner, dataset):    
        return issue_factories.Issue(user=owner,
                                    user_id=owner['id'],
                                    dataset_id=dataset['id'])

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report(self, app, joe_public, dataset, issue):
        env = {'REMOTE_USER': joe_public['name'].encode('ascii')}
        response = app.post(toolkit.url_for('forum.report',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
            extra_environ=env,
        )

        assert 'Issue reported to an administrator' in response.body


    @pytest.mark.usefixtures("clean_db", "issues_setup", "with_request_context")
    def test_report_as_admin(self, app, owner, dataset, issue):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.post(toolkit.url_for('forum.report',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
            extra_environ=env,
            follow_redirects=True
        )

        assert 'Report acknowledged. Marked as abuse/spam. Issue is invisible to normal users.'\
            in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_as_anonymous_user(self, app, dataset, issue):
        response = app.post(toolkit.url_for('forum.report',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
        )

        assert 'You must be logged in to report issues' in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_an_issue_that_does_not_exist(self, app, owner, dataset):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.post(toolkit.url_for('forum.report',
                                    dataset_id=dataset['id'],
                                    issue_number='1235455'),
            extra_environ=env,
            expect_errors=True
        )
        assert response.status_code == 404

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_clear(self, app, owner, dataset, issue):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.post(toolkit.url_for('issues_report_clear',
                                dataset_id=dataset['id'],
                                issue_number=issue['number']),
            extra_environ=env,
        )

        assert 'Issue report cleared' in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_clear_normal_user(self, app, dataset, issue):
        user = factories.User()
        model.Session.add(Issue.Report(user['id'],
                                      issue['id']))
        model.Session.commit()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.post(toolkit.url_for('issues_report_clear',
                                    dataset_id=dataset['id'],
                                    issue_number=issue['number']),
            extra_environ=env,
            expect_errors=True
        )

        assert 'Issue report cleared' in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_reset_on_issue_that_does_not_exist(self, app, owner, dataset):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.post(toolkit.url_for('issues_report_clear',
                                    dataset_id=dataset['id'],
                                    issue_number='1235455'),
            extra_environ=env,
            expect_errors=True
        )

        assert response.status_code == 404


class TestReportComment(object):
    @pytest.fixture
    def joe_public(self):
        return factories.User()

    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)

    @pytest.fixture
    def dataset(self, owner, org):
        return factories.Dataset(user=owner, owner_org=org['name'])

    @pytest.fixture
    def issue(self, owner, dataset):    
        return issue_factories.Issue(user=owner,
                                    user_id=owner['id'],
                                    dataset_id=dataset['id'])
    
    @pytest.fixture
    def comment(self, owner, dataset, issue):
        return issue_factories.IssueComment(
            user_id=owner['id'],
            dataset_id=dataset['id'],
            issue_number=issue['number'])

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report(self, app, joe_public, dataset, issue, comment):
        env = {'REMOTE_USER': joe_public['name'].encode('ascii')}
        response = app.post(toolkit.url_for('issues.report_comment',
                                dataset_id=dataset['id'],
                                issue_number=issue['number'],
                                comment_id=comment['id']),
            extra_environ=env,
        )

        assert 'Comment has been reported to an administrator' in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_as_admin(self, app, owner, dataset, issue, comment):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.post(
            url=toolkit.url_for('issues.report_comment',
                                dataset_id=dataset['id'],
                                issue_number=issue['number'],
                                comment_id=comment['id']),
            extra_environ=env,
        )

        assert 'Report acknowledged. Marked as abuse/spam. Comment is invisible to normal users.'\
             in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_not_logged_in(self, app, dataset, issue, comment):
        response = app.post(toolkit.url_for('issues.report_comment',
                                dataset_id=dataset['id'],
                                issue_number=issue['number'],
                                comment_id=comment['id']),
        )

        assert 'You must be logged in to report comments' in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_an_issue_that_does_not_exist(self, app, owner, dataset, comment):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.post(toolkit.url_for('issues.report_comment',
                                dataset_id=dataset['id'],
                                issue_number='1235455',
                                comment_id=comment['id']),
            extra_environ=env,
            expect_errors=True
        )

        assert response.status_code == 404

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_clear(self, app, owner, dataset, issue, comment):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.post(
            url=toolkit.url_for('issues.comment_report_clear',
                                dataset_id=dataset['id'],
                                issue_number=issue['number'],
                                comment_id=comment['id']),
            extra_environ=env,
        )

        assert 'Spam/abuse report cleared' in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_clear_state_normal_user(self, app, dataset, issue, comment):
        user = factories.User()
        model.Session.add(IssueComment.Report(user['id'], comment['id']))
        model.Session.commit()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.post(
            url=toolkit.url_for('issues.comment_report_clear',
                                dataset_id=dataset['id'],
                                issue_number=issue['number'],
                                comment_id=comment['id']),
            extra_environ=env,
        )

        assert 'Spam/abuse report cleared' in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_reset_on_issue_that_does_not_exist(self, app, owner, dataset):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.post(toolkit.url_for('issues.comment_report_clear',
                                dataset_id=dataset['id'],
                                issue_number='1235455',
                                comment_id='12312323'),
            extra_environ=env,
            expect_errors=True
        )

        assert response.status_code == 404
