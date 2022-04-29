import pytest
import mock

from ckan import model
from ckan.tests import factories, helpers

from ckanext.forums.tests import factories as issue_factories
from ckanext.forums.model import Issue, IssueComment
from ckanext.forums.exception import ReportAlreadyExists
from ckanext.forums.tests.fixtures import issues_setup, owner, user


class TestReportAnIssue(object):
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_an_issue(self, owner):
        org = factories.Organization(user=owner)
        dataset = factories.Dataset(owner_org=org['name'])
        issue = issue_factories.Issue(user_id=owner['id'],
                                      dataset_id=dataset['id'])

        user = factories.User(name='unauthed')
        context = {
            'user': user['name'],
            'model': model,
        }
        helpers.call_action(
            'forum_report',
            context=context,
            dataset_id=dataset['id'],
            issue_number=issue['number']
        )

        issue_obj = Issue.get(issue['id'])
        assert len(issue_obj.abuse_reports) == 1
        assert issue_obj.visibility == 'visible'

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_publisher_reports_an_issue(self, owner):
        '''this should immediately hide the issue'''
        org = factories.Organization(user=owner)
        dataset = factories.Dataset(owner_org=org['name'])
        issue = issue_factories.Issue(user=owner, user_id=owner['id'],
                                      dataset_id=dataset['id'])

        context = {
            'user': owner['name'],
            'model': model,
        }
        helpers.call_action(
            'forum_report',
            context=context,
            dataset_id=dataset['id'],
            issue_number=issue['number']
        )

        result = helpers.call_action(
            'forum_show',
            dataset_id=dataset['id'],
            issue_number=issue['number'],
        )
        assert 'hidden' == result['visibility']

    @mock.patch.dict('ckanext.forums.logic.action.action.config',
                     {'ckanext.forums.max_strikes': '0'})
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_max_strikes_hides_issues(self, owner):
            org = factories.Organization(user=owner)
            dataset = factories.Dataset(owner_org=org['name'])
            issue = issue_factories.Issue(user_id=owner['id'],
                                        dataset_id=dataset['id'])

            user_0 = factories.User()
            context = {
                'user': user_0['name'],
                'model': model,
            }
            helpers.call_action(
                'forum_report',
                context=context,
                dataset_id=dataset['id'],
                issue_number=issue['number']
            )

            user_1 = factories.User()
            context = {
                'user': user_1['name'],
                'model': model,
            }
            helpers.call_action(
                'forum_report',
                context=context,
                dataset_id=dataset['id'],
                issue_number=issue['number']
            )

            issue_obj = Issue.get(issue['id'])
            assert len(issue_obj.abuse_reports) == 2
            assert 'hidden' == issue_obj.visibility


class TestReportAnIssueTwice(object):
    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)

    @pytest.fixture
    def dataset(self, org):
        return factories.Dataset(owner_org=org['name'])
    
    @pytest.fixture
    def issue(self, owner, dataset):
        return issue_factories.Issue(user=owner,
                                    user_id=owner['id'],
                                    dataset_id=dataset['id'])

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_twice(self, owner, org, dataset, issue):
        user = factories.User(name='unauthed')
        context = {
            'user': user['name'],
            'model': model,
        }
        model.Session.begin_nested()
        helpers.call_action(
                'forum_report',
                context=context,
                dataset_id=dataset['id'],
                issue_number=issue['number']
        )
        pytest.raises(
                ReportAlreadyExists,
                helpers.call_action,
                'forum_report',
                context=context,
                dataset_id=dataset['id'],
                issue_number=issue['number']
        )


class TestIssueReportClear(object):

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_clear_as_publisher(self, owner):
        org = factories.Organization(user=owner)
        dataset = factories.Dataset(owner_org=org['name'])
        issue = issue_factories.Issue(user_id=owner['id'],
                                      dataset_id=dataset['id'],
                                      visibility='hidden')
        context = {
            'user': owner['name'],
            'model': model,
        }
        helpers.call_action(
            'forum_report_clear',
            context=context,
            dataset_id=dataset['id'],
            issue_number=issue['number']
        )
        result = helpers.call_action(
            'forum_show',
            dataset_id=dataset['id'],
            issue_number=issue['number'],
        )
        assert 'visible' == result['visibility']

        issue_obj = Issue.get(issue['id'])
        assert len(issue_obj.abuse_reports) == 0

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_clear_as_user(self, owner):
        org = factories.Organization(user=owner)
        dataset = factories.Dataset(owner_org=org['name'])
        issue = issue_factories.Issue(user_id=owner['id'],
                                      dataset_id=dataset['id'],
                                      visibility='hidden')
        user = factories.User()
        model.Session.add(Issue.Report(user['id'], issue['id']))
        model.Session.commit()
        context = {
            'user': user['name'],
            'model': model,
        }
        helpers.call_action(
            'forum_report_clear',
            context=context,
            dataset_id=dataset['id'],
            issue_number=issue['number']
        )
        result = helpers.call_action('forum_show',
                                     dataset_id=dataset['id'],
                                     issue_number=issue['number'])
        assert 'visible' == result['visibility']

        issue_obj = Issue.get(issue['id'])
        assert len(issue_obj.abuse_reports) == 0


class TestIssueReportShow(object):
    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)

    @pytest.fixture
    def dataset(self, org):
        return factories.Dataset(owner_org=org['name'])

    @pytest.fixture
    def issue(self, owner, dataset):
        issue = issue_factories.Issue(user_id=owner['id'],
                                    dataset_id=dataset['id'])
        context = {
            'user': owner['name'],
            'model': model,
        }
        helpers.call_action('forum_report',
                            context=context,
                            dataset_id=dataset['id'],
                            issue_number=issue['number'])
        return issue


    @pytest.fixture
    def user_0(self, dataset, issue):
        user_0 = factories.User()
        context = {
            'user': user_0['name'],
            'model': model,
        }
        helpers.call_action('forum_report', context=context,
                            dataset_id=dataset['id'],
                            issue_number=issue['number'])
        return user_0


    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_report_show_for_publisher(self, owner, user_0, dataset, issue):
        context = {
            'user': owner['name'],
            'model': model,
        }
        result = helpers.call_action(
            'forum_report_show',
            context=context,
            dataset_id=dataset['id'],
            issue_number=issue['number'],
        )
        print(result)
        assert set([owner['id'], user_0['id']]) == set(result)

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_report_show_for_user(self, user_0, dataset, issue):
        context = {
            'user': user_0['name'],
            'model': model,
        }
        result = helpers.call_action(
            'forum_report_show',
            context=context,
            dataset_id=dataset['id'],
            issue_number=issue['number'],
        )
        assert [user_0['id']] == result

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_report_show_for_other(self, dataset, issue):
        context = {
            'user': factories.User()['name'],
            'model': model,
        }
        result = helpers.call_action(
            'forum_report_show',
            context=context,
            dataset_id=dataset['id'],
            issue_number=issue['number'],
        )
        assert [] == result


class TestReportComment(object):
    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)

    @pytest.fixture
    def dataset(self, org):
        return factories.Dataset(owner_org=org['name'])
    
    @pytest.fixture
    def issue(self, owner, dataset):
        return issue_factories.Issue(user=owner,
                                    user_id=owner['id'],
                                    dataset_id=dataset['id'])

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_comment(self, owner, dataset, issue):
        comment = issue_factories.IssueComment(user_id=owner['id'],
                                               dataset_id=dataset['id'],
                                               issue_number=issue['number'])
        user = factories.User(name='unauthed')
        context = {
            'user': user['name'],
            'model': model,
        }
        helpers.call_action('forum_comment_report',
                            context=context,
                            dataset_id=dataset['id'],
                            issue_number=issue['number'],
                            comment_id=comment['id'])

        comment_obj = IssueComment.get(comment['id'])
        assert len(comment_obj.abuse_reports) == 1
        assert comment_obj.visibility == 'visible'

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_publisher_reports_a_comment(self, owner, org, dataset, issue):
        comment = issue_factories.IssueComment(user_id=owner['id'],
                                               dataset_id=dataset['id'],
                                               issue_number=issue['number'])
        context = {
            'user': owner['name'],
            'model': model,
        }
        helpers.call_action('forum_comment_report', context=context,
                            dataset_id=dataset['id'],
                            issue_number=issue['number'],
                            comment_id=comment['id'])

        result = helpers.call_action('forum_show',
                                     issue_number=issue['number'],
                                     dataset_id=dataset['id'])
        assert 'hidden' == result['comments'][0]['visibility']

    @mock.patch.dict('ckanext.forums.logic.action.action.config',
                     {'ckanext.forums.max_strikes': '0'})
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_max_strikes_hides_comment(self, owner, org, dataset, issue):
        comment = issue_factories.IssueComment(user_id=owner['id'],
                                               dataset_id=dataset['id'],
                                               issue_number=issue['number'])

        user = factories.User(name='unauthed')
        context = {
            'user': user['name'],
            'model': model,
        }
        helpers.call_action('forum_comment_report', context=context,
                            dataset_id=dataset['id'],
                            issue_number=issue['number'],
                            comment_id=comment['id'])
        result = helpers.call_action('forum_show',
                                     dataset_id=dataset['id'],
                                     issue_number=issue['number'])
        comment_obj = IssueComment.get(comment['id'])
        assert len(comment_obj.abuse_reports) == 1
        assert 'hidden' == result['comments'][0]['visibility']


class TestReportCommentTwice(object):
    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)

    @pytest.fixture
    def dataset(self, org):
        return factories.Dataset(owner_org=org['name'])
    
    @pytest.fixture
    def issue(self, owner, dataset):
        return issue_factories.Issue(user=owner,
                                    user_id=owner['id'],
                                    dataset_id=dataset['id'])
    
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_report_twice(self, owner, org, dataset, issue):
        comment = issue_factories.IssueComment(user_id=owner['id'],
                                              dataset_id=dataset['id'],
                                              issue_number=issue['number'])

        user = factories.User(name='unauthed')
        context = {
           'user': user['name'],
           'model': model,
        }
        helpers.call_action('forum_comment_report',
                           context=context,
                           dataset_id=dataset['id'],
                           issue_number=issue['number'],
                           comment_id=comment['id'])

        pytest.raises(
                    ReportAlreadyExists,
                    helpers.call_action,
                    'forum_comment_report',
                    context=context,
                    dataset_id=dataset['id'],
                    issue_number=issue['number'],
                    comment_id=comment['id'],
        )


class TestCommentReportClearAsPublisher(object):
    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)

    @pytest.fixture
    def dataset(self, org):
        return factories.Dataset(owner_org=org['name'])
    
    @pytest.fixture
    def issue(self, owner, dataset):
        return issue_factories.Issue(user=owner,
                                    user_id=owner['id'],
                                    dataset_id=dataset['id'])

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_clear_as_publisher(self, owner, org, dataset, issue):
        comment = issue_factories.IssueComment(user_id=owner['id'],
                                               dataset_id=dataset['id'],
                                               issue_number=issue['number'],
                                               visibility='hidden')
        context = {
            'user': owner['name'],
            'model': model,
        }
        model.Session.add(IssueComment.Report(owner['id'],
                                              parent_id=comment['id']))
        model.Session.commit()
        helpers.call_action('forum_comment_report_clear', context=context,
                            dataset_id=dataset['id'],
                            issue_number=issue['number'],
                            comment_id=comment['id'])
        result = helpers.call_action('forum_show',
                                     issue_number=issue['number'],
                                     dataset_id=dataset['id'])
        assert 'visible' == result['comments'][0]['visibility']
        comment_obj = IssueComment.get(comment['id'])
        model.Session.refresh(comment_obj)
        assert len(comment_obj.abuse_reports) == 0


class TestCommentReportClearAsUser(object):
    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)

    @pytest.fixture
    def dataset(self, org):
        return factories.Dataset(owner_org=org['name'])
    
    @pytest.fixture
    def issue(self, owner, dataset):
        return issue_factories.Issue(user=owner,
                                    user_id=owner['id'],
                                    dataset_id=dataset['id'])

    @pytest.mark.usefixtures("clean_db", "issues_setup")    
    def test_clear_as_user(self, owner, org, dataset, issue):
        comment = issue_factories.IssueComment(user_id=owner['id'],
                                               dataset_id=dataset['id'],
                                               issue_number=issue['number'])

        user = factories.User()
        model.Session.add(IssueComment.Report(user['id'],
                                              parent_id=comment['id']))
        model.Session.commit()
        context = {
            'user': user['name'],
            'model': model,
        }
        helpers.call_action('forum_comment_report_clear', context=context,
                            dataset_id=dataset['id'],
                            issue_number=issue['number'],
                            comment_id=comment['id'])

        comment_obj = IssueComment.get(comment['id'])
        assert len(comment_obj.abuse_reports) == 0
        assert 'visible' == comment_obj.visibility
