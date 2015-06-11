DEBUG = True
SECRET_KEY = 'some_secret'


# Map SSO attributes from ADFS to session keys under session['user']
SSO_ATTRIBUTE_MAP = {
  'HTTP_ADFS_LOGIN': (True, 'username'),
}
SSO_LOGIN_URL = '/login'
SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'