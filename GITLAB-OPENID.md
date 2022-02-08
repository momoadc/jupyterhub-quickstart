# Configuring GitLab openid authentication

In order to change the authentication of the jupyterhub to gitlab you need first to [create](https://docs.gitlab.com/ee/integration/oauth_provider.html) an applicaion in your user. The callback_url is ```https://{{ YOUR_HOST }}/hub/oauth_callback```.

You should get a client_id and client_secret. Put these in the ```c.GitLabOAuthenticator.client_id ``` and ```c.GitLabOAuthenticator.client_secret``` variablees in the ```jupyterhub_config-workspace.py``` file.

Then create a new image (customize the image name according to your remote registry name):
```
docker build -t jupyterhub .
```

Push it to a remote registry (docker.io for example):
```
docker push jupyterhub
```

Change the JUPYTERHUB_IMAGE in the deployment file (```templates/jupyterhub-deployment.yaml```) to the new image.

To apply the new image run:
```
oc process -f templates/jupyterhub-deployment.yaml | oc apply -f -
```

If you wish to delete a previous instance of jupyterhub before applying the new image or delete the new deployment to free resources run
```
oc process -f templates/jupyterhub-deployment.yaml | oc delete -f -
```
