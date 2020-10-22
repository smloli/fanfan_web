import socket
import threading
import urllib.parse
from lxml import etree
from fake_useragent import UserAgent
import requests
import os.path

class Novel():
    def __init__(self):
        ua = UserAgent()
        self.headers = {'UserAgent': ua.random}
        self.s = requests.session()

    def get_html(self,url):
        html = self.s.get(url, headers=self.headers)
        html.encoding = 'gbk'
        return html.text

    @staticmethod
    def get_xpath(url,http_server):
        http = 'https://bbs.fanfann.com/'
        space = '\u3000'
        html = etree.HTML(novel.get_html(url))
        # 帖子id
        url_cid = html.xpath("//a[@style='color:green;']/@href")
        if not url_cid:
            return None
        # 小说名
        novelName = html.xpath("//title/text()")
        novelName = novelName[0][:-18].replace('TXT下载 ', '')
        # 访问在线阅读
        html = etree.HTML(novel.get_html(http + url_cid[0]))
        # 判断Novel文件夹是否存在，不存在就创建
        if not os.path.exists('Novel'):
            os.mkdir('Novel')
        # 下载路径
        path = './Novel/' + novelName + '.txt'
        # 判断文件是否存在
        if os.path.exists(path):
            print(novelName + '，已下载！')
            return path
        # 文案
        wenan = html.xpath("//p[@class='intro']/text()")
        wenan = wenan[0].lstrip() + '\n'
        # 章节地址
        url = html.xpath("//ul[@class='cf']//li//a/@href")
        # 章节名
        title = html.xpath("//ul[@class='cf']//li//a/text()")
        # 标题计次
        i = 0
        # 去除文章简介
        url = url[1:]
        title = title[1:]
        lengh = len(url)
        with open(path, 'w', encoding='utf8') as f:
            f.write(wenan)
            for a in url:
                # 正文
                html = etree.HTML(novel.get_html(http + a))
                result = html.xpath('//div[@class="read-content j_readContent"]//text()')
                # 转换成字符串
                temp = ''.join(result)
                # 判断段落分隔符
                space = '    ' if '    ' not in temp else '\u3000'
                temp = temp.replace(space, '\n')
                f.write('\n' + title[i])
                f.write(temp)
                i += 1
        return path


class Server():
    def __init__(self):
        tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        tcp_server.bind(('', 9000))
        tcp_server.listen(128)
        self.tcp_server = tcp_server

    @staticmethod
    def _recv(http_server,ip_port):
        recv_data = http_server.recv(1024)
        if not recv_data:
            http_server.close
            return
        recv_content = recv_data.decode('utf-8')
        result_list = recv_content.split(' ', 2)
        path = result_list[1]
        if path == '/':
            path = '/download.html'
        Server._return_html(path,http_server,recv_content,ip_port)

    # 限制下载次数
    @staticmethod
    def veify(http_server,ip_port):
        ip_data = []
        try:
            with open('veify.data', 'r') as tmp:
                ip_data = eval(tmp.read())
        except Exception:
            ip_data.append({ip_port[0]: 0})
        index = 0
        for i in ip_data:
            for c in i.keys():
                ip_addr = c
            if ip_addr == ip_port[0]:
                if i[ip_port[0]] < 3:
                    with open('veify.data', 'w') as ip:
                        value = i[ip_port[0]]
                        ip_data[index][ip_port[0]] = value + 1
                        tmp = str(ip_data)
                        ip.write(tmp)
                        return False
                if i[ip_port[0]] >= 3:
                    response = ('HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n' + '\r\n' + '今日下载次数已达上限!').encode('utf-8')
                    Server._send(http_server,response)
                    return True
            index += 1

    # 返回数据给浏览器
    @staticmethod
    def _return_html(path,http_server,recv_content,ip_port):
        if recv_content[:4] == 'POST':
            url_info_index_left = recv_content.find('https')
            url = recv_content[url_info_index_left:]
            url = urllib.parse.unquote(url)
            if url.find('https://bbs.fanfann.com/') != -1:
                path = novel.get_xpath(url,http_server)
                if path!= None:
                    if Server.veify(http_server,ip_port):
                        return
                    with open(path, 'rb') as f:
                        file_data = f.read()
                        response_line = 'HTTP/1.1 200 OK\r\n'
                        response_header = 'Content-type: application/octet-stream\r\nContent-Disposition: attachment;filename=' + os.path.basename(path) +'\r\n'
                        response = (response_line + response_header + '\r\n').encode('utf-8') + file_data
                else:
                    response = ('HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n' + '\r\n' + '下载地址错误，文件资源不存在!').encode('utf-8')
                Server._send(http_server,response)
                return
        try:
            with open('.' + path, 'rb') as f:
                file_data = f.read()
                response_line = f'HTTP/1.1 200 OK\r\n'
        except FileNotFoundError:
            response_line = f'HTTP/1.1 404 Not Found\r\n'
            with open('404.html', 'rb') as f:
                file_data = f.read()
        response_header = 'Server: PPPloli\r\n'
        response = (response_line + response_header + '\r\n').encode('utf-8') + file_data
        Server._send(http_server,response)

    @staticmethod
    def _send(http_server,response):
        http_server.send(response)
        http_server.close()

    def run(self):
        while True:
            http_server, ip_port = self.tcp_server.accept()
            loli = threading.Thread(target=self._recv, args=(http_server,ip_port))
            loli.setDaemon(True)
            loli.start()


if __name__ == '__main__':
    server =Server()
    novel = Novel()
    server.run()