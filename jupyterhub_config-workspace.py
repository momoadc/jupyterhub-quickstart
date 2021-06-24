# Authenticate users against OpenShift OAuth provider.

from os import read


def get_ldap_groups(username):
    import ldap
    from ldap.filter import escape_filter_chars
    print("getting ldap groups for: " + username)
    # LDAP_SERVER = "ldap.server.com"
    # baseDN = "ou=people,dc=example,dc=com"
    # ldapObj = ldap.initialize('ldap://%s' % LDAP_SERVER)
    # userdn = ldapObj.search_s(baseDN,ldap.SCOPE_SUBTREE, "(|(&(objectClass=*)(sAMAccountName=%s)))" % username, ["distinguishedName",])
    # binaryGroups = ldapObj.search_s(baseDN,
    #                                 ldap.SCOPE_SUBTREE,
    #                                 "(member:1.2.840.113556.1.4.1941:={0})"
    #                                 .format(escape_filter_chars(userdn[0][1]['distinguishedName'][0].decode())),
    #                                 ['*',])
    # groups = [group[0] for group in binaryGroups]
    
    # usualy you'd want to return groups but here we're using mock data
    return [ 
        'cn=group1,ou=groups,dc=example,dc=com',
        'cn=group2,ou=groups,dc=example,dc=com',
        'cn=group3,ou=groups,dc=example,dc=com',
        'cn=group4,ou=groups,dc=example,dc=com',
        'cn=group5,ou=groups,dc=example,dc=com'
    ]

def read_config():
    import json

    configJson = {}
    with open("/opt/app-root/config.json", "r") as f:
        configJson = json.loads(f.read())
    
    return configJson



def get_resource_requirements(username):
    profiles=[
        {
            'display_name': 'DemoDEF - choose me!!',
            'slug': 'Demo-python',
            'default': True,
            'kubespawner_override': {
                'image': 'quay.io/ypery/jup-minimal-py38-notebook:latest',
                'cpu_limit': 1,
                'mem_limit': '512M',
            }
        },{
            'display_name': 'Training Env - Python',
            'slug': 'training-python',
            'default': True,
            'kubespawner_override': {
                'image': 'training/python:label',
                'cpu_limit': 1,
                'mem_limit': '512M',
            }
        }, {
            'display_name': 'Training Env - Datascience',
            'slug': 'training-datascience',
            'kubespawner_override': {
                'image': 'training/datascience:label',
                'cpu_limit': 2,
                'mem_limit': '1G',
            }
        }, {
            'display_name': 'DataScience - Small instance',
            'slug': 'datascience-small',
            'kubespawner_override': {
                'image': 'datascience/small:label',
                'cpu_limit': 3,
                'mem_limit': '2G',
            }
        }, {
            'display_name': 'DataScience - Medium instance',
            'slug': 'datascience-medium',
            'kubespawner_override': {
                'image': 'datascience/medium:label',
                'cpu_limit': 4,
                'mem_limit': '4G',
            }
        }
    ]
    
    userGroups = get_ldap_groups(username)    
    print(userGroups)
    config = read_config()
    print("config")
    print(config)
    for group in config['Groups']:
        if group['name'] in userGroups:
            profiles += group['profiles']
    print(profiles)
    return profiles

c.JupyterHub.authenticator_class = "openshift"

from oauthenticator.openshift import OpenShiftOAuthenticator
OpenShiftOAuthenticator.scope = ['user:full']

client_id = '%s-%s-users' % (application_name, namespace)
client_secret = os.environ['OAUTH_CLIENT_SECRET']

c.OpenShiftOAuthenticator.client_id = client_id
c.OpenShiftOAuthenticator.client_secret = client_secret
c.Authenticator.enable_auth_state = True

c.CryptKeeper.keys = [ client_secret.encode('utf-8') ]

c.OpenShiftOAuthenticator.oauth_callback_url = (
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
            'subPath': 'private-workspace'
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

    # Grab the OpenShift user access token from the login state.

    auth_state = yield spawner.user.get_auth_state()
    access_token = auth_state['access_token']

    # Set the session access token from the OpenShift login.

    pod.spec.containers[0].env.append(
            dict(name='OPENSHIFT_TOKEN', value=access_token))

    # See if a template for the project name has been specified.
    # Try expanding the name, substituting the username. If the
    # result is different then we use it, not if it is the same
    # which would suggest it isn't unique.

    project = os.environ.get('OPENSHIFT_PROJECT')

    if project:
        name = project.format(username=spawner.user.name)
        if name != project:
            pod.spec.containers[0].env.append(
                    dict(name='PROJECT_NAMESPACE', value=name))

            # Ensure project is created if it doesn't exist.

            pod.spec.containers[0].env.append(
                    dict(name='OPENSHIFT_PROJECT', value=name))

    return pod

def option_renderer(spawner):
    name = spawner.user.name
    print("name: " + name)
    return get_resource_requirements(name)

c.KubeSpawner.profile_list = option_renderer     


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
