# pixiv_crawler
利用cookie和作者的id来爬取作者的作品
#### 该爬虫使用方法：

##### 1.填写需要爬取的作者id

```python
 #填写作者id↓
    user_id = ''
    user_id = user_id.strip()
    #user_name = 'pudding'
```

##### 2.登录需要爬取的作者网站，从all?zhang=zh中获取headers的cookies

```python
    cookie = ''
    #填写需要的cookie↑
```

##### 3.更改存储地址

```python
#存储地址↓
file_dirs = r"E:\pics"
```

##### 4.修改相应的代理端口和header(这里的端口是我自己的端口和header)

```python
async def Gethttp(url,cookie,download):
    proxy = 'http://127.0.0.1:7890'
```

##### 5.运行即可

