# coding=utf-8
from gevent import monkey; monkey.patch_all()
from gevent import pool
# 下面这个模块是给mp3文件添加标签的，如：图片，作者，流派，还有歌词（歌词添加好像没用）什么的
from mutagen.id3 import APIC, TIT2, TPE1, TPE2, TALB, SYLT, TDRC, TCON, TRCK
from mutagen.mp3 import MP3

import requests
import os
import re
import queue
import time
import random

# import eyed3 # mp3文件添加tag


__author__ = "winner"
# 图片下载的根目录
BASE_DIR = "./data"
if not os.path.exists(BASE_DIR):
    os.mkdir(BASE_DIR)
# mp3下载线程数
MP3_DOWNLOAD_THREAD_NUM = 10

class KuwoCn(object):
    """酷我音乐爬虫"""
    def __init__(self, log_file_name="my.log"):
        # 默认的域名
        self.host = "http://www.kuwo.cn"
        # 根据关键字key获取歌曲的rid值的json数据的接口
        self.rid_url = "/api/www/search/searchMusicBykeyWord?key={}"
        # 根据rid获取歌曲下载链接的json数据的接口
        self.mp3_url = "/url?rid={}&type=convert_url3&br=128kmp3"
        # 获取音乐榜 可以得到sourceid
        self.bang_menu = "/api/www/bang/bang/bangMenu"
        # 获取音乐信息的接口
        self.music_info = "/api/www/music/musicInfo?mid={}"
        # 根据 musicid 获取歌词信息
        self.song_lyric = "http://m.kuwo.cn/newh5/singles/songinfoandlrc?musicId={}"
        # 根据bangid 获取音乐列表
        self.music_list = "/api/www/bang/bang/musicList?bangId={}&pn={}&rn={}"
        # 一些必要的请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
            "Referer": "http://www.kuwo.cn/search/list", # 这个请求头没有的话，会出现 403 Forbidden
            "csrf": "0HQ0UGKNAKR", # CSRF Token Not Found!
            # CSRF Token Not Found!
            "Cookie": "Hm_lvt_cdb524f42f0ce19b169a8071123a4797=1584003311; _ga=GA1.2.208068437.1584003311; _gid=GA1.2.1613688009.1584003311; Hm_lpvt_cdb524f42f0ce19b169a8071123a4797=1584017980; kw_token=0HQ0UGKNAKR; _gat=1",
        }
        # 多线程支持
        self.mp3_q = queue.Queue()
        # gevent
        self.pool1 = pool.Pool()
        self.pool2 = pool.Pool()
        # 自己的代理池
        self.proxies = [
            {'http': '116.114.19.204:443'},
            {'http': '101.231.104.82:80'},
            {'http': '116.114.19.211:443'},
            {'http': '84.17.47.190:80'},
        ]
        # 日志文件名
        # self.log_file_name = log_file_name
        self.f = open("{}/{}".format(BASE_DIR, log_file_name), "w", encoding="utf-8")
        self.f.write("log: use time second = minute = hour\n")
        # 过滤item["name"]中的无效字符
        self.invalid_characters = r"[/\?]"

    def __del__(self):
        self.f.close()

    def my_log(self, msg):
        """写一些日志文件"""
        self.f.write("[{}]: {}\n".format(time.strftime("%Y/%m%D %H:%M:%S", time.localtime()), msg))
        self.f.flush() # 由于写的比较少，所以可以刷新缓冲区，如果写的日志角度，那么就不用刷新缓冲区

    def my_get(self, url, stream=False):
        """自定义的请求函数，可以打印一些信息，和处理反爬"""
        response = requests.get(url, headers=self.headers, stream=stream)
        while response.status_code != 200:
            time.sleep(1)
            try:
                response = requests.get(url, headers=self.headers, stream=stream)
            except:
                pass
        # print("{} [{}]".format(response.url, response.status_code))
        return response

    def search_music_by_keyword(self, key):
        """
        根据关键字key获取歌曲的rid值的json数据的接口
        """
        # 这里默认从一堆的列表中选择第一个歌曲
        return self.my_get(self.host+self.rid_url.format(key)).json()["data"]["list"][0]

    def get_music_info(self, mid):
        """
        根据mid也就是rid，获取音乐信息
        经过筛选后的数据格式
        musicrid: "MUSIC_81010978"
        artist: "海伦"
        pic: "http://img2.kuwo.cn/star/albumcover/300/48/79/1272165134.jpg"
        isstar: 0
        rid: 81010978
        upPcStr: "kuwo://play/?play=MQ==&num=MQ==&musicrid0=TVVTSUNfODEwMTA5Nzg=&name0=x8Wx37nDxO8=&artist0=uqPC1w==&album0=x8Wx37nDxO8=&artistid0=MTA4MDAzMA==&albumid0=MTEzNzE4MjU=&playsource=d2ViwK3G8L/Nu6e2yy0+MjAxNrDmtaXH+tKz"
        duration: 183
        content_type: "0"
        mvPlayCnt: 451286
        track: 1
        hasLossless: true
        hasmv: 1
        releaseDate: "2019-11-09"
        album: "桥边姑娘"
        albumid: 11371825
        pay: "16515324"
        artistid: 1080030
        albumpic: "http://img2.kuwo.cn/star/albumcover/500/48/79/1272165134.jpg"
        songTimeMinutes: "03:03"
        isListenFee: false
        mvUpPcStr: "kuwo://play/?play=MQ==&num=MQ==&musicrid0=TVVTSUNfODEwMTA5Nzg=&name0=x8Wx37nDxO8=&artist0=uqPC1w==&album0=x8Wx37nDxO8=&artistid0=MTA4MDAzMA==&albumid0=MTEzNzE4MjU=&playsource=d2ViwK3G8L/Nu6e2yy0+MjAxNrDmtaXH+tKz&media=bXY="
        pic120: "http://img2.kuwo.cn/star/albumcover/120/48/79/1272165134.jpg"
        albuminfo: "海伦 最新单曲《桥边姑娘》。"
        name: "桥边姑娘"
        online: 1
        payInfo: {cannotOnlinePlay: 0, cannotDownload: 0}
        """
        return self.my_get(self.host+self.music_info.format(mid)).json()

    def get_song_lyric(self, musicid):
        """
        根据 musicid 也就是 rid 获取歌词信息
        主要的接口数据:
        {"data":{"lrclist":[{"time":"0.0","lineLyric":"不分手的恋爱 - 汪苏泷"}, "songinfo":{}
        返回值 [(text, time)]
        """
        time.sleep(random.randint(3, 7)) # 访问太快，会出现500的错误
        data =  self.my_get(self.song_lyric.format(musicid)).json()["data"]
        lrclist = []
        # {"data":null,"msg":"音乐查询失败","msgs":null,"profileid":"site","reqid":"081bc8bcXb67bX476aXa742X277424d2de4d","status":301}
        if data:
            lrclist = data["lrclist"] if data["lrclist"] else []
        lyric_filter = []
        for item in lrclist:
            lyric_filter.append((item["lineLyric"], int(float(item["time"])*1000)))        
        return lyric_filter

    def get_bang_menu_list(self):
        """
        获取所有的音乐榜单信息
        经过筛选后的数据格式
        [
            name: "官方榜",
            list: Array[5]
                {
                    "sourceid":"93",
                    "intro":"酷我用户每天播放线上歌曲的飙升指数TOP排行榜，为你展示流行趋势、蹿红歌曲，每天更新",
                    "name":"酷我飙升榜",
                    "id":"489929",
                    "source":"2",
                    "pic":"http://img3.kwcdn.kuwo.cn/star/upload/7/8/1584054363.png",
                    "pub":"今日更新"
                },
        ]
        """
        return self.my_get(self.host+self.bang_menu).json()["data"]

    def get_bang_menu_by_name(self, name):
        """
        通过名字获取一个总的榜单
        """
        bang_menu_list = self.get_bang_menu_list()
        for bang_menu in bang_menu_list:
            if bang_menu["name"].find(name) != -1:
                return bang_menu
        return {}

    def get_bang_by_name(self, name):
        """
        通过名字获取榜单，返回榜单中包含给定的名字的榜单
        """
        bang_menu_list = self.get_bang_menu_list()
        for bang_menu in bang_menu_list:
            for bang in bang_menu["list"]:
                if bang["name"].find(name) != -1:
                    return bang
        return {}

    def get_music_list(self, bangid, pn=1, rn=30):
        """
        根据榜单bangid, 获取音乐列表
        经过筛选后的数据格式
        num: "300" 这个榜单的总的歌词的数量，可以依据这个实现榜单所有歌词的爬取
        pub: "2020-03-13"
        musicList: [{musicrid: "MUSIC_80488731", artist: "阿冗", trend: "u0",…},…]
        """
        return self.my_get(self.host+self.music_list.format(bangid, pn, rn)).json()["data"]

    def get_mp3_download_url_by_rid(self, rid):
        """
        根据rid获取歌曲下载链接的json数据的接口
        code: 200
        msg: "success"
        url: "https://sz-sycdn.kuwo.cn/d38d5a334ea880471d34fc5ca17cf9af/5e6ae940/resource/n1/68/38/37304574.mp3"
        """
        mp3_url = self.my_get(self.host+self.mp3_url.format(rid)).json()["url"]
        while not mp3_url:
            mp3_url = self.my_get(self.host+self.mp3_url.format(rid)).json()["url"]
        return mp3_url

    def set_mp3_headers(self, full_file_name, item):
        """给mp3文件加入一些标签信息"""
        mp3 = MP3(full_file_name)
        # 参与创作的艺术家
        mp3["TPE1"] = TPE1(text=item["artist"])
        mp3["TPE2"] = TPE2(text=item["artist"])
        # 标题
        mp3["TIT2"] = TIT2(text=item["name"])
        # 发行日期
        mp3["TDRC"] = TDRC(text=item["releaseDate"])
        # 歌曲封面 atach picture
        mp3["APIC"] = APIC(mime='image/jpeg', type=3, data=self.my_get(item["albumpic"]).content)
        # 专辑
        mp3["TALB"] = TALB(text=item["album"])
        # 歌词 unsynchronised lyrics/text 因为不显示，所以就不设置了
        # mp3["SYLT"] = SYLT(text=self.get_song_lyric(item["rid"]), type=1, format=2, encoding=3)
        # 流派 genre 一共有148 0: Blues
        mp3["TCON"] = TCON(text=item["content_type"])
        # # 专辑中的排行
        mp3["TRCK"] = TRCK(text="{}/".format(item["track"]))
        mp3.save()

        # mp3 = eyed3.load(full_file_name)
        # # 参与创作的艺术家
        # mp3.tag.artist = item["artist"]
        # mp3.tag.album_artist = item["artist"]
        # # 标题
        # mp3.title = item["name"]
        # # 发行日期
        # # mp3["TDRC"] = TDRC(text=item["releaseDate"])
        # # 歌曲封面 atach picture
        # mp3.tag.images.set(type_=0x10, img_data=self.my_get(item["albumpic"]).content, mime_type="image/jpeg")
        # # 专辑
        # mp3.tag.album = item["album"]
        # # 歌词 Synchronised lyrics/text
        # f = open("1.lrc", encoding="utf-8")
        # mp3.tag.lyrics.set(text=f.read())
        # # 流派 genre
        # # mp3["TCON"] = TCON(text=item["content_type"])
        # mp3.tag.save(encoding="utf-8")

    def download_lyric(self, folder, item, lyric_list):
        """
        根据lyric_list列表和item，解析为标准的歌词格式 [M:S.ms]lyric的格式, floder 是指定存放的文件夹，相对于BASE_DIR
        一些特殊的头
        [ar:歌手名]、[ti:歌曲名]、[al:专辑名]、[by:编辑者(指lrc歌词的制作人)]、[offset:时间补偿值] 
        （其单位是毫秒，正值表示整体提前，负值相反。这是用于总体调整显示快慢的，但多数的MP3可能不会支持这种标签）
        """
        name = "{}.lrc".format(re.sub(self.invalid_characters, "-", item["name"])) # 处理一些非法的文件名
        lyric_file_name = "{}/{}/{}".format(BASE_DIR, folder, name)
        # 如果文件存在，退出
        if os.path.exists(lyric_file_name):
            print("{} already exists.".format(lyric_file_name))
            return
        # 内容
        content = []
        # 一些特殊的头
        content.append("[ar:{}]".format(item["artist"]))
        content.append("[ti:{}]".format(item["name"]))
        content.append("[al:{}]".format(item["album"]))
        content.append("[by:{}]".format(__author__))
        # content.append("[offset:0]")
        # 歌词内容
        for text, time in lyric_list:
            ms = time % 1000 // 10 # 毫秒
            s = time // 1000  % 60 # 秒
            m = time // 1000 // 60 # 分
            content.append("[%.2d:%.2d.%.2d]%s" % (m, s, ms, text))
        # 写入到文件
        f = open(lyric_file_name, "w", encoding="utf-8")
        for c in content:
            f.write("{}\n".format(c))
        f.close()
        print("{} write successfully.".format(name))

    def download_mp3(self, folder, item, url):
        """根具歌曲名称和下载歌曲的url，下载歌曲"""
        # 设置下载的文件名
        file_name = "{}.mp3".format(re.sub(self.invalid_characters, "-", item["name"])) # 处理一些非法的文件名
        full_file_name = "{}/{}/{}".format(BASE_DIR, folder, file_name)
        # 如果文件已经存在，直接返回
        if os.path.exists(full_file_name):
            print("{} already exists.".format(full_file_name))
            return
        f = open(full_file_name, "wb")
        # 发送请求，一定要设置strem=True，表示下载的是一个大文件
        response = self.my_get(url, stream=True)
        # 获取文件大小)
        file_size = int(response.headers["Content-Length"])/1024/1024 # 单位M
        # 已经下载的文件大小
        download_size = 0
        # 下载显示的一些符号
        download_symbol = r"\|/"
        # 控制这些符号需要的一些属性
        s, s_l = 0, len(download_symbol)
        # 迭代获取获取的内容
        for chunk in response.iter_content(chunk_size=1024):
            download_size += f.write(chunk)
            # 显示到屏幕的下载信息
            print("\rdownload %s %s ... %.2fM/%.2fM" %
                (file_name, download_symbol[s], download_size/1024/1024, file_size), end="")
            s = (s+1) % s_l
        f.close()
        print("\tok.")
        # 设置mp3头
        self.set_mp3_headers(full_file_name, item)

    def download_mp3_and_lyric(self, folder, item):
        """
        下载mp3同时下载对应的歌词
        """
        self.download_mp3(folder, item, self.get_mp3_download_url_by_rid(item["rid"]))
        self.download_lyric(folder, item, self.get_song_lyric(item["rid"]))

    def download_mp3_by_keyworld(self, key, key_folder="key"):
        """
        根据关键词语，下载歌曲，默认参数 key_folder 指定歌曲下载点的文件夹
        """
        # 创建一个文件夹
        folder = "{}/{}".format(BASE_DIR, key_folder)
        if not os.path.exists(folder):
            os.mkdir(folder)
        item = self.search_music_by_keyword(key)
        download_url = self.get_mp3_download_url_by_rid(item["rid"])
        self.download_mp3(key_folder, item, download_url)

    def __download_mp3_and_lyric_multithread(self, folder):
        """多线程下载歌曲和歌词"""
        while True:
            item = self.mp3_q.get()
            self.download_mp3_and_lyric(folder, item)
            self.mp3_q.task_done() # 发送一次任务完成的信号
            if self.mp3_q.empty():
                break

    def download_mp3_by_bang_multithread(self, folder, bang, num=30):
        """
        folder 指定榜单存放的目录
        根据榜单bang，下载歌曲，默认前30首，如果小于30，下载的为30首，这里也可以一个榜单的歌曲都下载下来。
        """
        # 判断folder文件夹是否存在
        dir_ = "{}/{}".format(BASE_DIR, folder)
        if not os.path.exists(dir_):
            os.mkdir(dir_)
        # 创建榜单文件夹
        bang_dir = "{}/{}/{}".format(BASE_DIR, folder, bang["name"])
        if not os.path.exists(bang_dir):
            os.mkdir(bang_dir)
        # 根据 MP3_DOWNLOAD_THREAD_NUM 创建线程
        for _ in range(MP3_DOWNLOAD_THREAD_NUM):
            self.pool1.apply_async(func=self.__download_mp3_and_lyric_multithread, 
                    args=("{}/{}".format(folder, bang["name"]),))
        # 统计开始时间
        start_time = time.time()

        pn, rn = 1, 30 # 默认一页30首
        already_download_num = 0
        while already_download_num <= num-rn:
            data = self.get_music_list(bang["sourceid"], pn, rn)
            for music in data["musicList"]:
                # self.download_mp3_and_lyric(bang["name"], music)
                self.mp3_q.put(music)
            already_download_num = pn*rn
            pn += 1
        # 不足30首的部分
        rn = num - already_download_num
        if rn > 0:
            data = self.get_music_list(bang["sourceid"], pn, rn)
            for music in data["music_list"]:
                # self.download_mp3_and_lyric(bang["name"], music)
                self.mp3_q.put(music)
        # 等待线程结束
        self.mp3_q.join() # 等待队列为空
        # for t in mp3_download_thread_list:
            # t.join()
        self.pool1.join()
        # 统计用时
        use_time = time.time() - start_time
        msg = "download one bang %s use time %.2fs = %.2fm = %.2fh" % (bang["name"], use_time, use_time/60, use_time/3600)
        self.my_log(msg)
        print(msg)
            
    def download_mp3_by_bang_menu(self, bang_menu):
        """
        下载一个总榜单的音乐, 这个api由于想要使用多进程但是，还是用线程
        """
        # 创建总榜单文件夹
        bang_menu_folder = "{}/{}".format(BASE_DIR, bang_menu["name"])
        if not os.path.exists(bang_menu_folder):
            os.mkdir(bang_menu_folder)
        # 统计开始时间
        start_time = time.time()
        for bang in bang_menu["list"]:
            self.download_mp3_by_bang_multithread(bang_menu["name"], bang)
        # 统计用时
        use_time = time.time() - start_time
        msg = "download bang menu %s use time %.2fs = %.2fm = %.2fh" % (bang_menu["name"], use_time, use_time/60, use_time/3600)
        self.my_log(msg)
        print(msg)

    def download_mp3_all(self):
        # 下载所有的总榜
        start_time = time.time()
        bang_menu_list = self.get_bang_menu_list()
        for bang_menu in bang_menu_list:
            self.pool2.apply_async(func=self.download_mp3_by_bang_menu, args=(bang_menu,))
        self.pool2.join()
        use_time = time.time() - start_time
        self.my_log("ues total time: %.2fs = %.2fm = %.2fh" % (use_time, use_time/60, use_time/3600))

if __name__ == "__main__":
    kuwo = KuwoCn()
    # kuwo.download_mp3_by_keyworld("冬眠")
    # item = kuwo.search_music_by_keyword("不分手的恋爱") # rid 945320
    # music_info = kuwo.get_music_info(67733609)
    # print(music_info)
    # bang_menu = kuwo.get_bang_menu_list()
    # print(bang_menu)
    # bang = kuwo.get_bang_by_name("酷我新歌榜")
    # kuwo.download_mp3_by_bang_multithread("bang_test", bang)
    # lyric = kuwo.get_song_lyric(item["rid"])
    # print(lyric)
    # kuwo.download_lyric("key", item, lyric)
    # kuwo.set_mp3_headers("./data/key/冬眠.mp3", item)
    # kuwo.download_mp3_and_lyric("key", item)
    # bang_menu = kuwo.get_bang_menu_by_name("全球榜")
    # print(bang_menu)
    # kuwo.download_mp3_by_bang_menu(bang_menu)
    # print(kuwo.my_get(kuwo.song_lyric.format(945320)).content.decode("utf-8")) # rid 67733609
    kuwo.download_mp3_all()

    