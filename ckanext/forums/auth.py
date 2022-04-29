from ckanext.forums.tests.logic.action.test_issue import dataset
from ckan import model
import ckan.plugins as p
from ckanext.forums import model as issue_model


def forum_auth(context, data_dict, privilege='package_update'):
    '''Returns whether the current user is allowed to do the action
    (privilege).'''
    auth_data_dict = dict(data_dict)
    # we're checking package access so it is dataset/package id
    auth_data_dict['id'] = auth_data_dict['dataset_id']
    try:
        return {'success': True}
    except p.toolkit.NotAuthorized:
        return {
            'success': False,
            'msg': p.toolkit._(
                'User {0} not authorized for action on issue {1}'.format(
                    str(context['user']),
                    auth_data_dict['id']
                )
            )
        }


@p.toolkit.auth_allow_anonymous_access
def forum_show(context, data_dict):
    return forum_auth(context, data_dict, 'package_show')


@p.toolkit.auth_allow_anonymous_access
def forum_search(context, data_dict):
    try:
        p.toolkit.check_access('package_search', context, dict(data_dict))
        return {'success': True}
    except p.toolkit.NotAuthorized:
        return {
            'success': False,
            'msg': p.toolkit._(
                'User {0} not authorized for action'.format(
                    str(context['user'])
                )
            )
        }

@p.toolkit.auth_allow_anonymous_access
def forum_create(context, data_dict):
    # Any logged in user
    return {'success': bool(context['user'])}

@p.toolkit.auth_allow_anonymous_access
def forum_comment_create(context, data_dict):
    return {'success': bool(context['user'])}
    # return issue_auth(context, data_dict, 'package_create')


@p.toolkit.auth_allow_anonymous_access
def forum_update(context, data_dict):
    '''Checks that we can update the issue.

    Those with update rights on dataset (dataset 'editors') plus issue owner
    can do general updates

    Updating issue status is only dataset 'editors'
    '''
    
    # now check if we created the issue
    issue = issue_model.Issue.get_by_number(
        issue_number=data_dict['issue_number'],
        dataset_id=data_dict['dataset_id'],
    )
    user = context['user']
    if not issue:
        return {'success': False}
    user_obj = model.User.get(user)
    if ((issue.user_id == user_obj.id) and # we're the creator
        # we are not trying to change status
       not (data_dict.get('status')
            and (issue.status != data_dict['status']))):
        return {'success': True}
    # all other cases not allowed
    return {
        'success': False,
        'msg': p.toolkit._(
            'User {user} not authorized for action on issue {issue}'.format(
                user=str(user),
                issue=data_dict['issue_number'])
            )
    }


@p.toolkit.auth_disallow_anonymous_access
def forum_delete(context, data_dict):
    try:
        issue_number = data_dict['issue_number']
    except KeyError:
        issue_number = data_dict['issue_id']

    issue = issue_model.Issue.get_by_number(
        issue_number=issue_number,
        dataset_id=data_dict['dataset_id'],
    )
    if issue is None:
        return forum_auth(context, data_dict)
    user = context['user']
    user_obj = model.User.get(user)
    if (issue.user_id == user_obj.id):
        return {'success': True}
    return forum_auth(context, data_dict)


@p.toolkit.auth_disallow_anonymous_access
def forum_report(context, data_dict):
    return {'success': True}


@p.toolkit.auth_disallow_anonymous_access
def forum_report_clear(context, data_dict):
    return {'success': True}


@p.toolkit.auth_disallow_anonymous_access
def forum_admin(context, data_dict):
    '''Who can administrate and issue

    sysadmins/organization admins and organization editors'''
    return forum_auth(context, data_dict)


@p.toolkit.auth_allow_anonymous_access
def forum_comment_search(context, data_dict):
    return {'success': True}
