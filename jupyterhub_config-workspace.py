from oauthenticator.gitlab import GitLabOAuthenticator
c.JupyterHub.authenticator_class = GitLabOAuthenticator
c.GitLabOAuthenticator.oauth_callback_url = 'https://jupyterhub-jupyterhub.apps.lcc570vo.eastus.aroapp.io/hub/oauth_callback'
c.GitLabOAuthenticator.client_id = 'e39314580b14d1f6d6bf77ae02f21bb140faabda53aa4385c2a145ec8d7eb604'
c.GitLabOAuthenticator.client_secret = 'f49367ca99eaebe0493f5a204923b998c036cbb497aba095fd355ddac9a8625b'
c.GitLabOAuthenticator.scope = ['openid']
c.GitLabOAuthenticator.scope = ['api read_repository write_repository']

# async def add_auth_env(spawner):
#     '''
#     We set user's id, login and access token on single user image to
#     enable repository integration for JupyterHub.
#     See: https://gitlab.com/gitlab-org/gitlab-foss/issues/47138#note_154294790
#     '''
#     auth_state = await spawner.user.get_auth_state()

#     if not auth_state:
#         spawner.log.warning("No auth state for %s", spawner.user)
#         return

#     spawner.environment['GITLAB_ACCESS_TOKEN'] = auth_state['access_token']
#     spawner.environment['GITLAB_USER_LOGIN'] = auth_state['gitlab_user']['username']
#     spawner.environment['GITLAB_USER_ID'] = str(auth_state['gitlab_user']['id'])
#     spawner.environment['GITLAB_USER_EMAIL'] = auth_state['gitlab_user']['email']
#     spawner.environment['GITLAB_USER_NAME'] = auth_state['gitlab_user']['name']

# c.KubeSpawner.pre_spawn_hook = add_auth_env