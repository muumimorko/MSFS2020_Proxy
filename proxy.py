import ssl
import os
from aiohttp import web
import aiohttp
from bingtile import QuadKeyToTileXY
from pathlib import Path
import os.path
from os import path
# Allow normal user to bind to port 443
# echo 'net.ipv4.ip_unprivileged_port_start=0' > /etc/sysctl.conf
# sudo sysctl --system

# domains
# weather.prod.kittyhawk.msgamestudios.com
# kh-k8s-prod-cdn.azureedge.net
# khstorelive.azureedge.net (CGLS)
# enc.dev.virtualearth.net (AERIAL, COLOR CORRECTION, ???)


Google=False
accessedurlscounts = {}
conn = aiohttp.TCPConnector(limit=30,limit_per_host=6)
session=aiohttp.ClientSession(connector=conn)

async def putToCache(data,name,provider):
    Path(os.path.dirname(f"/mnt/tiles/Users/teemu/source/repos/MSFS2020_CGLTools/cache/{provider}/{name}")).mkdir(parents=True, exist_ok=True)
    outfile=open(f"/mnt/tiles/Users/teemu/source/repos/MSFS2020_CGLTools/cache/{provider}/{name}",'wb')
    outfile.write(data)
async def readFromCache(name,provider):
    if path.exists(f"/mnt/tiles/Users/teemu/source/repos/MSFS2020_CGLTools/cache/{provider}/{name}"):
        datafile=open(f"/mnt/tiles/Users/teemu/source/repos/MSFS2020_CGLTools/cache/{provider}/{name}",'rb')
        return datafile.read()
    else:
        return -1

async def googleTile(request):
    res = await readFromCache(request.path,'google')
    if res != -1:
        rheaders = {}
        rheaders['X-VE-TILEMETA-CaptureDateMaxYYMM'] = '1504'
        rheaders['X-VE-TILEMETA-CaptureDatesRange'] = '5/21/2010-4/10/2015'
        rheaders['X-VE-TILEMETA-Product-IDs'] = '138'
        rheaders['ETag'] = "5887"
        rheaders['Content-Type'] = 'image/jpeg'
        print(f'Cache Google {request.path}')
        return web.Response(body=res, status=200, headers=rheaders)
    else:
        qkey = request.path[request.path.rindex(
                '/a')+2:request.path.rindex('.')]
        xy=QuadKeyToTileXY(qkey)
        headers = {}
        for hdr in request.raw_headers:
            headers[hdr[0].decode("utf-8")] = hdr[1] .decode("utf-8")
        r= await session.get(f'https://mt1.google.com/vt/lyrs=s&x={xy[0]}&y={xy[1]}&z={xy[2]}',allow_redirects=True)
        print(f'{request.url}')
        rheaders = {}
        rheaders['X-VE-TILEMETA-CaptureDateMaxYYMM'] = '1504'
        rheaders['X-VE-TILEMETA-CaptureDatesRange'] = '5/21/2010-4/10/2015'
        rheaders['X-VE-TILEMETA-Product-IDs'] = '138'
        rheaders['ETag'] = "5887"
        rheaders['Content-Type'] = 'image/jpeg'
        for hdr in r.headers:
            rheaders[hdr] = r.headers[hdr]
        data=await r.content.read()
        await putToCache(data,request.path,'google')
        return web.Response(body=data, status=200, headers=rheaders)


async def handle(request):
    global accessedurlscounts
    if 'tiles/a' in request.path:
        if Google:
            return await googleTile(request)
        else:
            qkey = request.path[request.path.rindex(
                '/a')+2:request.path.rindex('.')]
            xy=QuadKeyToTileXY(qkey)
            if os.path.isfile(f'/mnt/tiles/Users/teemu/source/repos/MSFS2020_CGLTools/tilesmod/{xy[2]}/{xy[0]}/{xy[1]}.jpg'):
                f = open(
                    f'/mnt/tiles/Users/teemu/source/repos/MSFS2020_CGLTools/tilesmod/{xy[2]}/{xy[0]}/{xy[1]}.jpg', 'rb')
                data = f.read()
                f.close()
                rheaders = {}
                rheaders['Content-Length'] = str(len(data))
                rheaders['X-VE-TILEMETA-CaptureDateMaxYYMM'] = '1504'
                rheaders['X-VE-TILEMETA-CaptureDatesRange'] = '5/21/2010-4/10/2015'
                rheaders['X-VE-TILEMETA-Product-IDs'] = '138'
                rheaders['ETag'] = "5887"
                rheaders['Content-Type'] = 'image/jpeg'
                print(f'Local {request.path}')
                return web.Response(body=data, status=200, headers=rheaders)
            else:
                if len(qkey)>17:
                    return web.Response(status=404)
                res = await readFromCache(request.path,'bing')
                if res != -1:
                    rheaders = {}
                    rheaders['X-VE-TILEMETA-CaptureDateMaxYYMM'] = '1504'
                    rheaders['X-VE-TILEMETA-CaptureDatesRange'] = '5/21/2010-4/10/2015'
                    rheaders['X-VE-TILEMETA-Product-IDs'] = '138'
                    rheaders['ETag'] = "5887"
                    rheaders['Content-Type'] = 'image/jpeg'
                    print(f'Cache Bing {request.path}')
                    return web.Response(body=res, status=200, headers=rheaders)
                else:
                    headers = {}
                    for hdr in request.raw_headers:
                        headers[hdr[0].decode("utf-8")] = hdr[1] .decode("utf-8")
                    r= await session.get(request.url,allow_redirects=True, headers=headers)
                    print(f'{request.url}')
                    rheaders = {}
                    for hdr in r.headers:
                        rheaders[hdr] = r.headers[hdr]
                    data=await r.content.read()
                    await putToCache(data,request.path,'bing')
                    return web.Response(body=data, status=200, headers=rheaders)
    else:
        headers = {}
        for hdr in request.raw_headers:
            headers[hdr[0].decode("utf-8")] = hdr[1] .decode("utf-8")
        if 'yuvworld' in request.path:
            byterange=request.headers['Range']
            rangestart=int(byterange[byterange.index('=')+1:byterange.index('-')])
            rangestop=int(byterange[byterange.index('-')+1:])
            lengthbytes=rangestop-rangestart+1
            infile=open('/mnt/tiles/Users/teemu/source/repos/MSFS2020_Proxy/yuvworld.cgl','rb')
            infile.seek(rangestart)
            data=infile.read(lengthbytes)
            infile.close()
            rheaders = {}
            rheaders['Content-Length'] = str(len(data))
            rheaders['Content-Type']='application/octet-stream'
            rheaders['Content-Range']=f'bytes {rangestart}-{rangestop}/{Path("/mnt/tiles/Users/teemu/source/repos/MSFS2020_Proxy/yuvworld.cgl").stat().st_size}'   
            print(request.url)
            print(f"Read bytes {rangestart} - {rangestop}")
            return web.Response(body=data, status=200, headers=rheaders)
            #return web.Response(status=404)
        if 'tsom_cc_activation_masks' in request.path:
            print(request.url)
            print("Skip color corrector mask")
            return web.Response(text='', status=404)
        if 'texture_synthesis_online_map_high_res' in request.path:
            print(request.url)
            print("Skip texture synthesis")
            return web.Response(text='', status=404)
        if 'mean_downsampling' in request.path:
            if '120120' in request.path:
                datafile=open(f"/mnt/tiles/Users/teemu/source/repos/MSFS2020_Proxy/yuv120120.png",'rb')
                data=datafile.read()
                return web.Response(body=data, status=200)
            else:
                return web.Response(status=404)
        if 'color_corrected_images' in request.path and 'cgl' in request.path:
            print(request.url)
            print("Skip cci")
            return web.Response(text='', status=404)
        if 'color_correction_matrices' in request.path:
            print(request.url)
            print("Skip ccm")
            return web.Response(text='', status=404)
        if 'results/v1.11.0/genid/a.xml' in request.path:
            r= await session.get(request.url,allow_redirects=True, headers=headers)
            rheaders = {}
            for hdr in r.headers:
                rheaders[hdr] = r.headers[hdr]
            infile=open(f"/mnt/tiles/Users/teemu/source/repos/MSFS2020_Proxy/a.xml",'rb')
            data=infile.read()
            print(f'MODIFIED {request.url}')
            rheaders['Content-Length']=str(len(data))
            return web.Response(body=data, status=200, headers=rheaders)
        r= await session.get(request.url,allow_redirects=True, headers=headers)
        rheaders = {}
        for hdr in r.headers:
            rheaders[hdr] = r.headers[hdr]
        data=await r.content.read()
        print(f'{request.url}')
        return web.Response(body=data, status=200, headers=rheaders)


app = web.Application()
app.add_routes([web.get('/{tail:.*}', handle), ])


ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain('server.pem')

web.run_app(app, ssl_context=ssl_context, port=443)
