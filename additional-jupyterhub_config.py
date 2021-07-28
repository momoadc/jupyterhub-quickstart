def get_ldap_groups(username):
  import ldap
  from ldap.filter import escape_filter_chars
  LDAP_SERVER = "ldap.server.com"
  baseDN = "ou=people,dc=example,dc=com"
  ldapUser = ""
  ldapPassword = ""
  ldapObj = ldap.initialize('ldap://%s' % LDAP_SERVER)
  ldapObj.simple_bind_s(ldapUser, ldapPassword)
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
      'description': 'quay.io/ypery/jup-pyspark-py37-notebook:latest - 1 CPU & 512M RAM',
      'default': True,
      'kubespawner_override': {
        'image': 'quay.io/ypery/jup-pyspark-py37-notebook:latest',
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
  config = read_config()
  for group in config['Groups']:
      if group['name'] in userGroups:
          profiles += group['profiles']
  return profiles

def option_renderer(spawner):
  name = spawner.user.name
  return get_resource_requirements(name)

c.KubeSpawner.profile_list = option_renderer     