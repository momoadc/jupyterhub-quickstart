# Authenticate users against Gitlab OAuth provider.
from oauthenticator.gitlab import GitLabOAuthenticator

c.JupyterHub.authenticator_class = GitLabOAuthenticator

GitLabOAuthenticator.scope = ['api']

c.GitLabOAuthenticator.client_id = '' #INSERT HERE THE CLIENT_ID AS IN THE APPLICATIONS SCOPE IN GITLAB
c.GitLabOAuthenticator.client_secret = '' #INSERT HERE THE CLIENT_SECRET AS IN THE APPLICATIONS SCOPE IN GITLAB
c.Authenticator.enable_auth_state = True

c.CryptKeeper.keys = [ client_secret.encode('utf-8') ]

c.GitLabOAuthenticator.oauth_callback_url = (
        'https://%s/hub/oauth_callback' % public_hostname)

# Add any additional JupyterHub configuration settings.

c.KubeSpawner.extra_labels = {
    'spawner': 'workspace',
    'class': 'session',
    'user': '{username}'
}

# Set up list of registered users and any users nominated as admins.

if os.path.exists('/opt/app-root/configs/admin_users.txt'):
    with open('/opt/app-root/configs/admin_users.txt') as fp:
        content = fp.read().strip()
        if content:
            c.Authenticator.admin_users = set(content.split())

if os.path.exists('/opt/app-root/configs/user_whitelist.txt'):
    with open('/opt/app-root/configs/user_whitelist.txt') as fp:
        c.Authenticator.whitelist = set(fp.read().strip().split())

# For workshops we provide each user with a persistent volume so they
# don't loose their work. This is mounted on /opt/app-root, so we need
# to copy the contents from the image into the persistent volume the
# first time using an init container.

volume_size = os.environ.get('JUPYTERHUB_VOLUME_SIZE')

if volume_size:
    c.KubeSpawner.pvc_name_template = c.KubeSpawner.pod_name_template

    c.KubeSpawner.storage_pvc_ensure = True

    c.KubeSpawner.storage_capacity = volume_size

    c.KubeSpawner.storage_access_modes = ['ReadWriteOnce']

    c.KubeSpawner.volumes.extend([
        {
            'name': 'data',
            'persistentVolumeClaim': {
                'claimName': c.KubeSpawner.pvc_name_template
            }
        }
    ])

    c.KubeSpawner.volume_mounts.extend([
        {
            'name': 'data',
            'mountPath': '/opt/app-root',
            'subPath': 'workspace'
        }
    ])

    c.KubeSpawner.init_containers.extend([
        {
            'name': 'setup-volume',
            'image': '%s' % c.KubeSpawner.image_spec,
            'command': [
                '/opt/app-root/bin/setup-volume.sh',
                '/opt/app-root',
                '/mnt/workspace'
            ],
            "resources": {
                "limits": {
                    "memory": os.environ.get('NOTEBOOK_MEMORY', '128Mi')
                },
                "requests": {
                    "memory": os.environ.get('NOTEBOOK_MEMORY', '128Mi')
                }
            },
            'volumeMounts': [
                {
                    'name': 'data',
                    'mountPath': '/mnt'
                }
            ]
        }
    ])

# Make modifications to pod based on user and type of session.

from tornado import gen

@gen.coroutine
def modify_pod_hook(spawner, pod):
    pod.spec.automount_service_account_token = True

    # Grab the Gitlab user access token from the login state.

    auth_state = yield spawner.user.get_auth_state()
    access_token = auth_state['access_token']

    # Set the session access token from the Gitlab login.

    pod.spec.containers[0].env.append(
            dict(name='GITLAB_TOKEN', value=access_token))

    # See if a template for the project name has been specified.
    # Try expanding the name, substituting the username. If the
    # result is different then we use it, not if it is the same
    # which would suggest it isn't unique.

    project = os.environ.get('GITLAB_PROJECT')

    if project:
        name = project.format(username=spawner.user.name)
        if name != project:
            pod.spec.containers[0].env.append(
                    dict(name='PROJECT_NAMESPACE', value=name))

            # Ensure project is created if it doesn't exist.

            pod.spec.containers[0].env.append(
                    dict(name='GITLAB_PROJECT', value=name))

    return pod

c.KubeSpawner.modify_pod_hook = modify_pod_hook

# Setup culling of terminal instances if timeout parameter is supplied.

idle_timeout = os.environ.get('JUPYTERHUB_IDLE_TIMEOUT')

if idle_timeout and int(idle_timeout):
    cull_idle_servers_cmd = ['/opt/app-root/bin/cull-idle-servers']

    cull_idle_servers_cmd.append('--timeout=%s' % idle_timeout)

    c.JupyterHub.services.extend([
        {
            'name': 'cull-idle',
            'admin': True,
            'command': cull_idle_servers_cmd,
        }
    ])
