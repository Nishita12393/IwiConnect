import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    @staticmethod
    def get_app_name():
        return os.getenv('APP_NAME', 'IwiConnect')

    @staticmethod
    def get_logo_url():
        return os.getenv('LOGO_URL', 'https://i.ibb.co/WL00tgn/iwiconnect-logo.png')

    @staticmethod
    def get_from_email():
        return os.getenv('FROM_EMAIL', 'IwiConnect <noreply@iwiconnect.local>')

    @staticmethod
    def get_db_name():
        return os.getenv('DB_NAME', 'iwi_web')

    @staticmethod
    def get_db_user():
        return os.getenv('DB_USER', 'root')

    @staticmethod
    def get_db_password():
        return os.getenv('DB_PASSWORD', 'toor')

    @staticmethod
    def get_db_host():
        return os.getenv('DB_HOST', 'localhost')

    @staticmethod
    def get_db_port():
        return os.getenv('DB_PORT', '3306')

    @staticmethod
    def get_email_host():
        return os.getenv('EMAIL_HOST', 'sandbox.smtp.mailtrap.io')

    @staticmethod
    def get_email_port():
        return os.getenv('EMAIL_PORT', '587')

    @staticmethod
    def get_email_user():
        return os.getenv('EMAIL_HOST_USER', '')

    @staticmethod
    def get_email_password():
        return os.getenv('EMAIL_HOST_PASSWORD', '')

    @staticmethod
    def get_email_use_tls():
        return os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'

    @staticmethod
    def get_email_use_ssl():
        return os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true' 