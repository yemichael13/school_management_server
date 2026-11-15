from datetime import timedelta
from pathlib import Path
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config('SECRET_KEY', default='dev-only-change-me')
DEBUG = config('DEBUG', default='True').lower() in ('1', 'true', 'yes', 'on')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','django.contrib.postgres','rest_framework_simplejwt.token_blacklist','corsheaders','rest_framework','django_filters','drf_spectacular','apps.accounts.apps.AccountsConfig','apps.core.apps.CoreConfig','apps.academics.apps.AcademicsConfig','apps.students.apps.StudentsConfig','apps.teachers.apps.TeachersConfig','apps.marks.apps.MarksConfig','apps.reports.apps.ReportsConfig','apps.promotions.apps.PromotionsConfig','apps.qr.apps.QRConfig','apps.files.apps.FilesConfig','apps.notifications.apps.NotificationsConfig','apps.audit.apps.AuditConfig','apps.exports.apps.ExportsConfig','apps.attendance.apps.AttendanceConfig']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','corsheaders.middleware.CorsMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR / 'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'
DATABASES = {'default': {'ENGINE':'django.db.backends.postgresql','NAME':config('DB_NAME',default='schoolmanagement'),'USER':config('DB_USER',default='postgres'),'PASSWORD':config('DB_PASSWORD',default=''),'HOST':config('DB_HOST',default='localhost'),'PORT':config('DB_PORT',default=5432,cast=int),'OPTIONS':{'sslmode':config('DB_SSLMODE',default='prefer')},'CONN_MAX_AGE':config('DB_CONN_MAX_AGE',default=60,cast=int)}}
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
AUTH_USER_MODEL = 'accounts.User'
LANGUAGE_CODE = config('LANGUAGE_CODE',default='en-us')
TIME_ZONE = config('TIME_ZONE',default='Africa/Addis_Ababa')
USE_I18N = True
USE_TZ = True
STATIC_URL = config('STATIC_URL',default='/static/')
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = config('MEDIA_URL',default='/media/')
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES':('rest_framework_simplejwt.authentication.JWTAuthentication',),'DEFAULT_PERMISSION_CLASSES':('rest_framework.permissions.IsAuthenticated',),'DEFAULT_FILTER_BACKENDS':('django_filters.rest_framework.DjangoFilterBackend','rest_framework.filters.SearchFilter','rest_framework.filters.OrderingFilter'),'DEFAULT_SCHEMA_CLASS':'drf_spectacular.openapi.AutoSchema','DEFAULT_PAGINATION_CLASS':'rest_framework.pagination.PageNumberPagination','PAGE_SIZE':config('API_PAGE_SIZE',default=25,cast=int)}
SIMPLE_JWT = {'ACCESS_TOKEN_LIFETIME':timedelta(minutes=config('JWT_ACCESS_MINUTES',default=30,cast=int)),'REFRESH_TOKEN_LIFETIME':timedelta(days=config('JWT_REFRESH_DAYS',default=1,cast=int)),'ROTATE_REFRESH_TOKENS':True,'BLACKLIST_AFTER_ROTATION':True,'UPDATE_LAST_LOGIN':True}
SPECTACULAR_SETTINGS = {'TITLE':'Degnetu Student Mark Management API','DESCRIPTION':'Backend API foundation for the student mark management system.','VERSION':'0.1.0','SERVE_INCLUDE_SCHEMA':False}
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS',default='http://localhost:5173,http://127.0.0.1:5173',cast=Csv())
CORS_ALLOW_CREDENTIALS = False
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT',default=False,cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE',default=False,cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE',default=False,cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS',default=0,cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS',default=False,cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD',default=False,cast=bool)






PASSWORD_RESET_TIMEOUT = config('PASSWORD_RESET_TIMEOUT', default=3600, cast=int)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@degnetu.local')
FRONTEND_PASSWORD_RESET_URL = config('FRONTEND_PASSWORD_RESET_URL', default='http://localhost:5173/reset-password')
FRONTEND_EMAIL_VERIFICATION_URL = config('FRONTEND_EMAIL_VERIFICATION_URL', default='http://localhost:5173/verify-email')

