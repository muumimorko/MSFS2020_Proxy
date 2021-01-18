import sys
import http.server
import ssl
import requests
import logging
import urllib3
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)

#domains
# weather.prod.kittyhawk.msgamestudios.com
# kh-k8s-prod-cdn.azureedge.net
# khstorelive.azureedge.net (CGLS)
# enc.dev.virtualearth.net (AERIAL, COLOR CORRECTION, ???)

class S(http.server.BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/octet-stream')
        self.end_headers()
    def do_GET(self):
        print(self.headers)
        targethost = self.headers['host']
        logging.info(f'https://{targethost}{self.path}')
        headers = self.headers
        # bing image handling
        if targethost == 'kh.ssl.ak.tiles.virtualearth.net':
                if '/a' in self.path:
                    qkey = self.path[self.path.rindex('/a')+2:self.path.rindex('.')]
                    if os.path.isfile(f'tiles/{qkey}.jpg'):
                        f = open(f'tiles/{qkey}.jpg', 'rb')
                        print("localTile")
                        self.send_response(200)
                        self.send_header('Content-type', 'image/jpeg')
                        self._headers_buffer.pop(1)
                        self._headers_buffer.pop(1)
                        self.end_headers()
                        data = f.read()
                        self.wfile.write(data)
                        f.close()
                    else:
                        r = requests.get(f'https://{targethost}{self.path}',
                                    allow_redirects=True, verify=False, headers=headers)
                        self.send_response(200)
                        self._headers_buffer.pop(1)
                        self._headers_buffer.pop(1)
                        for hdr in r.headers:
                            self.send_header(hdr,r.headers[hdr])
                        self.end_headers()
                        self.wfile.write(r.content)
                else:
                    r = requests.get(f'https://{targethost}{self.path}',
                                allow_redirects=True, verify=False, headers=headers)
                    self.send_response(200)
                    self._headers_buffer.pop(1)
                    self._headers_buffer.pop(1)
                    for hdr in r.headers:
                        self.send_header(hdr,r.headers[hdr])
                    self.end_headers()
                    self.wfile.write(r.content)
        else:
            r = requests.get(f'https://{targethost}{self.path}',
                             allow_redirects=True, verify=False, headers=headers)
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self._headers_buffer.pop(1)
            self._headers_buffer.pop(1)
            for hdr in r.headers:
                self.send_header(hdr,r.headers[hdr])
            self.end_headers()
            self.wfile.write(r.content)


# server_address = ('0.0.0.0', 443)
# httpd = http.server.HTTPServer(server_address, S)
# httpd.socket = ssl.wrap_socket(
#     httpd.socket, server_side=True, certfile='server.pem', ssl_version=ssl.PROTOCOL_TLS)
# httpd.serve_forever()


from aiohttp import web
import ssl
import requests
import os

accessedurlscounts={}

async def handle(request):
    global accessedurlscounts
    if '/a' in request.path:
        print("image")
        qkey = request.path[request.path.rindex('/a')+2:request.path.rindex('.')]
        if os.path.isfile(f'/mnt/tiles/Users/teemu/source/repos/MSFS2020_CGLTools/tiles/{qkey}.jpg'):
            f = open(f'/mnt/tiles/Users/teemu/source/repos/MSFS2020_CGLTools/tiles/{qkey}.jpg', 'rb')
            print("localTile")
            data = f.read()
            f.close()
            rheaders={}
            rheaders['Content-Length']=str(len(data))
            rheaders['X-VE-TILEMETA-CaptureDateMaxYYMM']='1504'
            rheaders['X-VE-TILEMETA-CaptureDatesRange']='5/21/2010-4/10/2015'
            rheaders['X-VE-TILEMETA-Product-IDs']= '138'
            rheaders['ETag']="5887"
            rheaders['Content-Type']='image/jpeg'
            return web.Response(body=data,status=200,headers=rheaders)
        else:
            headers={}
            for hdr in request.raw_headers:
                headers[hdr[0].decode("utf-8") ]=hdr[1] .decode("utf-8")
            if 'yuvworld' in request.path or 'tsom_cc_activation_masks' in request.path:
                print("Skip color corrector")
                return web.Response(text='',status=404)
            r = requests.get(request.url,
                                    allow_redirects=True, headers=headers)
            if request.url in accessedurlscounts:
                accessedurlscounts[request.url]+=1
            else:
                accessedurlscounts[request.url]=1
            print(f'{accessedurlscounts[request.url]} {request.url}')
            rheaders={}
            for hdr in r.headers:
                rheaders[hdr]=r.headers[hdr]
            return web.Response(body=r.content,status=200,headers=rheaders)
    else:
        headers={}
        for hdr in request.raw_headers:
            headers[hdr[0].decode("utf-8") ]=hdr[1] .decode("utf-8")
        if 'yuvworld' in request.path or 'tsom_cc_activation_masks' in request.path:
            print("Skip color corrector")
            return web.Response(text='',status=404)
        r = requests.get(request.url,
                                allow_redirects=True, headers=headers)
        if request.url in accessedurlscounts:
            accessedurlscounts[request.url]+=1
        else:
            accessedurlscounts[request.url]=1
        print(f'{accessedurlscounts[request.url]} {request.url}')
        rheaders={}
        for hdr in r.headers:
            rheaders[hdr]=r.headers[hdr]
        return web.Response(body=r.content,status=200,headers=rheaders)


app = web.Application()
app.add_routes([web.get('/{tail:.*}', handle),])


ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain('server.pem')

web.run_app(app, ssl_context=ssl_context, port=443)