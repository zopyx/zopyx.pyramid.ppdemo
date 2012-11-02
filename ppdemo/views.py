import os
import mimetypes
import tempfile
from webob import Response
from pyramid.view import view_config
from zopyx.smartprintng.client.zip_client import Proxy2 as Proxy

@view_config(route_name='home', renderer='templates/index.pt')
def index(request):
    return {'project':'pp-demo'}

@view_config(name='contact', renderer='templates/contact.pt')
def contact(request):
    return {'project':'pp-demo'}

@view_config(name='demo', renderer='templates/demo.pt')
def demo(request):
    return {'project':'pp-demo'}

@view_config(name='references', renderer='templates/references.pt')
def references(request):
    return {'project':'pp-demo'}

@view_config(name='documentation', renderer='templates/documentation.pt')
def documentation(request):
    return {'project':'pp-demo'}

@view_config(name='about', renderer='templates/about.pt')
def about(request):
    return {'project':'pp-demo'}

def build_html(ident, **kw):
    filename = os.path.join(os.path.dirname(__file__), 'pdf-templates', '%s.pt' % ident)
    html = open(filename).read() 
    html = unicode(html, 'utf-8')
    html = html % kw
    return html.encode('utf-8')

@view_config(name='generate-pdf')
def generate_pdf(request):
    ident = str(request.params.get('ident'))
    args = dict([(str(k), str(request.params.get(k, ''))) for k in request.params if k not in ('ident',)])
    html = build_html(ident, **args)

    proxy = Proxy('http://demo:demo@pp-server.zopyx.com')
    dname = tempfile.mkdtemp()
    fname = os.path.join(dname, 'index.html')
    file(fname, 'wb').write(html)

    result = proxy.convertZIP2(dname, converter_name='pdf-pdfreactor')
    output_filename = result['output_filename']
    ct, dummy = mimetypes.guess_type(output_filename)
    basename, ext = os.path.splitext(output_filename)
    converter = 'pdf-pdfreactor'
    headers = [('content-disposition','attachment; filename=%s-%s%s' % (ident, converter,ext)), 
               ('content-type', ct)]
    return Response(body=file(output_filename, 'rb').read(),
            content_type=ct,
            headerlist=headers)
