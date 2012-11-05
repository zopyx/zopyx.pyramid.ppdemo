from pyramid.config import Configurator

from kotti import conf_defaults as default_settings


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings2 = default_settings.copy()
    settings2.update(settings) 
    config = Configurator(settings=settings2)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.include('pyramid_mailer')
    config.add_route('home', '/')
    config.scan()
    return config.make_wsgi_app()
