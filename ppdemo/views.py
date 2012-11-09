import os
import re
import json
import shutil
import mimetypes
import tempfile
import mimetypes
from webob import Response
from pyramid.view import view_config
import pyramid.httpexceptions as exc
import lxml.html
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

@view_config(name='about', renderer='templates/about.pt')
def about(request):
    return {'project':'pp-demo'}

@view_config(name='sent-mail-success', renderer='templates/contact-success.pt')
def contact_success(request):
    return {'project':'pp-demo'}


@view_config(name='send-mail')
def send_mail(request):
    from pyramid_mailer import get_mailer
    from pyramid_mailer.message import Message
    mailer = get_mailer(request)
    body = '%s\n%s\n%s' % (request.params['fullname'],
                           request.params['email'],
                           request.params['message'])

    message = Message(subject=request.params['subject'],
                      sender='admin@produce-and-publish.com',
                      recipients=['info@zopyx.com'],
                      body=body)
    mailer.send(message)
    raise exc.HTTPFound('sent-mail-success')

def build_html(ident, **kw):
    filename = os.path.join(os.path.dirname(__file__), 'pdf-templates', '%s.pt' % ident)
    html = open(filename).read() 
    return html % kw

def fix_image_links(html, view_name):
    """ We need to convert '../_images/xx.gif' links into  'images/xx.gif' etc. """
    root = lxml.html.fromstring(html)
    for img in root.xpath('.//img'):
        src = img.attrib['src']
        src = '/%s/%s' % (view_name, re.sub('(.*_images)', '_images', src))
        img.attrib['src'] = src
    return lxml.html.tostring(root, encoding=unicode)


view_config(name='generate-pdf')
def generate_pdf(request):

    ident = str(request.params.get('ident'))
    converter_name = str(request.params.get('converter_name', 'pdf-pdfreactor'))

    args = dict([(str(k), request.params.get(k, u'').encode('utf-8')) for k in request.params if k not in ('ident',)])
    html = build_html(ident, **args)

    proxy = Proxy('http://demo:demo@pp-server.zopyx.com')
#    proxy = Proxy('http://localhost:6543')
    dname = tempfile.mkdtemp()
    fname = os.path.join(dname, 'index.html')
    file(fname, 'wb').write(html)

    # copy stylesheets
    templ_dir = os.path.join(os.path.dirname(__file__), 'pdf-templates')
    for fn in os.listdir(templ_dir):
        base, ext = os.path.splitext(fn)
        if ext in ('.css', '.ttf'):
            shutil.copy(os.path.join(templ_dir, fn), dname)

    result = proxy.convertZIP2(dname, converter_name=converter_name)
    output_filename = result['output_filename']
    ct, dummy = mimetypes.guess_type(output_filename)
    basename, ext = os.path.splitext(output_filename)
    headers = [('content-disposition','attachment; filename=%s-%s%s' % (ident, converter_name, ext)), 
               ('content-type', ct)]
    return Response(body=file(output_filename, 'rb').read(),
            content_type=ct,
            headerlist=headers)


def render_sphinx(request, docroot, subdir='', view_name=''):
    """ This traverser renders a Sphinx content page stored as
        JSON below the 'documentation_json_' directory. The documentation
        is generated from Sphinx using the JSON builder 
        (or just "make json")
    """

    if not os.path.exists(docroot):
        raise ValueError('%s does not exist' % docroot)

    json_root = os.path.join(docroot, 'build', 'json', subdir)
    image_root = os.path.join(docroot, 'build', 'json', '_images')

    dir_subpath = str(os.path.sep.join(request.subpath[:-1]))
    last_item = str(request.subpath[-1])
    base, ext = os.path.splitext(last_item)
    json_filename = last_item + '.fjson'
    docpath = os.path.join(json_root, dir_subpath, json_filename)
    if os.path.exists(docpath):
        d = json.loads(file(docpath, 'rb').read())
        d['body'] = fix_image_links(d['body'], view_name)
        return d
    else:
        if dir_subpath.startswith('_images'):
            docpath = os.path.join(image_root, last_item)
        else:
            docpath = os.path.join(json_root, dir_subpath, last_item)
        content_type = 'image/%s' % ext[1:]
        content_type, encoding = mimetypes.guess_type(docpath)
        headers = [('content-type', content_type)]
        return Response(body=file(docpath, 'rb').read(),
                        content_type=content_type,
                        headerlist=headers)

@view_config(name='documentation', renderer='templates/sphinx.pt')
def docs(request, docroot='pp-docs'):
    """ This traverser renders a Sphinx content page stored as
        JSON below the 'documentation_json_' directory. The documentation
        is generated from Sphinx using the JSON builder 
        (or just "make json")
    """
    docroot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'parts', 'documentation-checkout', docroot))
    return render_sphinx(request, docroot, '', view_name='documentation')
        
@view_config(name='references', renderer='templates/sphinx.pt')
def references(request, docroot='www.produce-and-publish.com'):
    """ docroot = root of the SVN Sphinx checkout.
        subdir = root of the subdirectory below <docroot>/build/json
    """
    docroot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'parts', 'documentation-checkout', docroot))
    return render_sphinx(request, docroot, 'references', view_name='references')
