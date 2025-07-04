from .config import Config

def get_app_name():
    return Config.get_app_name()

def get_logo_url():
    return Config.get_logo_url()

def get_from_email():
    return Config.get_from_email() 