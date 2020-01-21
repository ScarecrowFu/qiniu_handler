# 说明

上传文件或网络文件到七牛

# 安装依赖

```bash
pip install qiniu requests fake_headers
```

# 使用方法

可选择是否配置 ```config.txt```

若配置 ```config.txt```,  请按以下方式编写配置文件

```
[QINIU]
access_key = access_key
secret_key = secret_key
domain = domain
bucket_name = bucket_name
```

```bash
python qiniu_handler.py -l {local_file} -b {bucket} -a {access_key} -s {secret_key} -d {domain}
```

```bash
python qiniu_handler.py -u {file_url} -b {bucket} -a {access_key} -s {secret_key} -d {domain}
```

# 参数说明

```bash
usage: qiniu_handler.py [-h] [-l LOCAL_FILE] [-p LOCAL_PATH] [-u URL]
                        [-b BUCKET_NAME] [-k KEY_NAME] [-d DOMAIN]
                        [-a ACCESS_KEY] [-s SECRET_KEY] [-db DOWNLOAD_BUCKET]
                        [-sp SAVE_PATH]

A script that upload file to qiniu 上传方式分为本地文件和url链接

optional arguments:
  -h, --help            show this help message and exit
  -l LOCAL_FILE, --local_file LOCAL_FILE
                        需要上传的文件路径
  -p LOCAL_PATH, --local_path LOCAL_PATH
                        需要上传的文件夹路径
  -u URL, --url URL     需要上传的文件的url地址
  -b BUCKET_NAME, --bucket_name BUCKET_NAME
                        七牛存储空间名称
  -k KEY_NAME, --key_name KEY_NAME
                        上传后的名字, 为空的由程序生成
  -d DOMAIN, --domain DOMAIN
                        七牛存储空间域名,为空使用程序默认
  -a ACCESS_KEY, --access_key ACCESS_KEY
                        qiniu access_key, 为空使用程序默认
  -s SECRET_KEY, --secret_key SECRET_KEY
                        qiniu secret_key, 为空使用程序默认
  -db DOWNLOAD_BUCKET, --download_bucket DOWNLOAD_BUCKET
                        下载指定空间的所有文件
  -sp SAVE_PATH, --save_path SAVE_PATH
                        下载文件的指定路径, 默认为当前目录
```
