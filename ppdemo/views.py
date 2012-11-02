import os
import mimetypes
import tempfile
from webob import Response
from pyramid.view import view_config
from zopyx.smartprintng.client.zip_client import Proxy2 as Proxy

@view_config(route_name='home', renderer='templates/index.pt')
def index(request):
    return {'project':'pp-demo'}

def build_html(ident, **kw):
    filename = os.path.join(os.path.dirname(__file__), 'pdf-templates', '%s.pt' % ident)
    html = open(filename).read() 
    html = unicode(html, 'utf-8')
    html = html % kw
    return html.encode('utf-8')

@view_config(name='generate-pdf')
def generate_pdf(request):
    text = request.params.get('text', '')
    ident = str(request.params.get('ident', ''))
    html = build_html(ident, text=text)

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
