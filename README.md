## 酷我音乐 [http://www.kuwo.cn/](http://www.kuwo.cn/)

### 1. 分析音乐下载的接口

[http://www.kuwo.cn/url?format=mp3&rid=81010978&response=url&type=convert_url3&br=128kmp3&from=web&t=1584003980221&reqId=xxxxxxxxxxxxxxxxxx](http://www.kuwo.cn/url?format=mp3&rid=81010978&response=url&type=convert_url3&br=128kmp3&from=web&t=1584003980221&reqId=xxxxxxxxxxxxxxxxxx)

```python
{
	"format": "mp3", # 音频格式
	"rid": "81010978", # 音乐的id
	"response": "url",
	"type": "convert_url3",
	"br": "128kmp3", 
	"from": "web", # 来源
	"t": "15840xxxxx60779", # 时间戳
	"reqId": "xxxxxxxxxxxxxxxxxx", # 请求id
}
```

经过测试剔除了一些参数 http://www.kuwo.cn/url?rid={}&type=convert_url3&br=128kmp3

下面这是响应的`json`数据

`{"code": 200, "msg": "success", "url": "https://sz-sycdn.kuwo.cn/96f635b8ea7045ffe7f1dec9baa4cf4d/5e6a0115/resource/n1/68/38/37304574.mp3"}`

请求返回了一个`json`数据，从这里我们可以看到，该**音乐`id`**对应的请求的`url`，由于可以在新的标签页打开这个请求，可以看出这里的请求反爬几乎没有

### 2. 分析如何获取歌曲的`rid`值

#### 2.1 根据关键字获取`rid`值

[http://www.kuwo.cn/api/www/search/searchMusicBykeyWord?key=%E4%B8%80%E4%B8%AA%E4%BA%BA%E5%BE%88%E5%A5%BD&pn=1&rn=30&reqId=xxxxxxxxxxxxxxxxxx](http://www.kuwo.cn/api/www/search/searchMusicBykeyWord?key=%E4%B8%80%E4%B8%AA%E4%BA%BA%E5%BE%88%E5%A5%BD&pn=1&rn=30&reqId=xxxxxxxxxxxxxxxxxx)

通过浏览器访问时，出现了`403 Forbidden`的响应，应该是做了一些反爬措施，经过测试，剔除了一些参数得到 http://www.kuwo.cn/api/www/search/searchMusicBykeyWord?key={}

#### 2.2 通过获取音乐列表的接口获取`rid`值

[http://www.kuwo.cn/api/www/bang/bang/musicList?bangId=93&pn=1&rn=30&reqId=xxxxxxxxxxxxxxxxxx](http://www.kuwo.cn/api/www/bang/bang/musicList?bangId=93&pn=1&rn=30&reqId=xxxxxxxxxxxxxxxxxx)

这个接口需要`cookie`头和`csrf`头，从浏览器copy一下就可以了（应该是比较`cookie`里面的`csrf`值和`csrf`头里面的值是否相同）

````python
{
	"bangId": "93", # 酷我飙升榜
	"pn": "1", # 页数
	"rn": "30", # 一页的歌曲数
	"reqId": "xxxxxxxxxxxxxxxxxx", # 请求的id
}
````

由于获取音乐列表是通过`bangid`获取，所以要找到获取`bangid`的接口

#### 2.3 获取所有的音乐排行榜的接口

[http://www.kuwo.cn/api/www/bang/bang/bangMenu ](http://www.kuwo.cn/api/www/bang/bang/bangMenu) 找到这个接口优点巧合

这个接口里面的`sourceid`就对应了`bangid`值

这个接口需要`cookie`头和`csrf`头，从浏览器copy一下就可以了（应该是比较`cookie`里面的`csrf`值和`csrf`头里面的值是否相同），就是处理一下`csrf`，**直接访问会出现**`{"success":false,"message":"CSRF Token Not Found!","now":"2020-03-xxx:00:xxx"}`

来一张图

<img src="G:\mypython\酷我音乐\images\bang_menu.png" alt="音乐榜单信息" style="zoom: 80%;" />

从这里，我们可以算一下，如果每一个**子榜单**下载前**30首歌**那么一会下载的歌曲数目为：

* 子榜单数目: `5 + 13 + 6 + 5 + 9 + 2 = 40`
* 歌曲总数: `40 * 30 = 1200`
* 每首歌曲的大小大约为: `4M`
* 整个下下来的数据的大小为: `4800M = 4800/1024~= 4.69G`

### 3. 一些其他的接口

#### 3.1 根据音乐`mid`值获取音乐信息

[http://www.kuwo.cn/api/www/music/musicInfo?mid=81010978&reqId=xxxxxxxxxxxxxxxxxx](http://www.kuwo.cn/api/www/music/musicInfo?mid=81010978&reqId=xxxxxxxxxxxxxxxxxx)

这个接口需要剔除的参数很少，就一个`reqid`应该是标识的身份信息

```python
{
	"mid": "81010978", # 音乐的mid值 和 rid 相同
	"reqId": "xxxxxxxxxxxxxxxxxx", # 请求的id
}
```

这个接口需要`cookie`头和`csrf`头，从浏览器copy一下就可以了（应该是比较`cookie`里面的`csrf`值和`csrf`头里面的值是否相同）

#### 3.2 获取歌词的接口

[http://m.kuwo.cn/newh5/singles/songinfoandlrc?musicId=80488731&reqId=xxxxxxxxxxxxxxxxxx](http://m.kuwo.cn/newh5/singles/songinfoandlrc?musicId=80488731&reqId=xxxxxxxxxxxxxxxxxx)

这个接口新建一个标签就可以访问了。

```json
{"data":{"lrclist":[{"time":"0.0","lineLyric":"《你的答案》"},{"time":"2.46","lineLyric":"作词 Lyrics：林晨阳 刘涛"},{"time":"4.69","lineLyric":"作曲 Music：刘涛"},{"time":"7.34","lineLyric":"演唱Singer：阿冗"},{"time":"9.32","lineLyric":"制作人 Produced by 刘涛"},{"time":"12.09","lineLyric":"编曲 Arranger：谭侃侃"},{"time":"14.6","lineLyric":"吉他 Guitar：谭侃侃"},{"time":"15.15","lineLyric":"键盘 Keyboards：谭侃侃"},{"time":"17.44","lineLyric":"合声 Backing vocals：金天 胡阁"},{"time":"18.95","lineLyric":"录音棚 Recording studio：北京好乐无荒录音棚"},{"time":"19.65","lineLyric":"录音师 Recording Engineer：吴佳敏"},{"time":"20.35","lineLyric":"混音师 Mixing Engineer：刘三斤"},{"time":"21.59","lineLyric":"母带后期混音师 Mastering Engineer：刘三斤"},{"time":"22.2","lineLyric":"监制 Executive producer: 陶诗"},{"time":"23.0","lineLyric":"OP/SP：好乐无荒"},{"time":"24.0","lineLyric":"封面设计：kidult."},{"time":"24.82","lineLyric":"鸣谢：万物体验家；不要音乐"},{"time":"25.24","lineLyric":"也许世界就这样"},{"time":"28.49","lineLyric":"我也还在路上"},{"time":"31.13","lineLyric":"没有人能诉说"},{"time":"36.21","lineLyric":"也许我只能沉默"},{"time":"39.25","lineLyric":"眼泪湿润眼眶"},{"time":"42.1","lineLyric":"可又不甘懦弱"},...
```
