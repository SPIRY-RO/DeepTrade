from urllib import parse, request


class ServerJiao:
    @staticmethod
    def send_server_warn(desp,text='主人服务器又挂掉啦~'):
        textmod={'text':text,'desp':desp}
        textmod = parse.urlencode(textmod)
        print(textmod)
        #输出内容:user=admin&password=admin
        header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko'}
        url='https://sc.ftqq.com/SCU16599Tcb92a58cbbdc088d88500f0a37cec5a95a18d54f94f4a.send'
        req = request.Request(url='%s%s%s' % (url,'?',textmod),headers=header_dict)
        res = request.urlopen(req)
        res = res.read()
        print(res)
        #输出内容(python3默认获取到的是16进制'bytes'类型数据 Unicode编码，如果如需可读输出则需decode解码成对应编码):b'\xe7\x99\xbb\xe5\xbd\x95\xe6\x88\x90\xe5\x8a\x9f'
        print(res.decode(encoding='utf-8'))
        #输出内容:登录成功