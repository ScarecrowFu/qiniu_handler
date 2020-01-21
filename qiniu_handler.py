"""
desc:
    上传文件或网络文件到七牛
auth:
    Alan
requirements:
    pip install qiniu requests fake_headers
"""
from qiniu import Auth, put_file, BucketManager
import os
import hashlib
import pathlib
import requests
import shutil
from mimetypes import guess_extension
import argparse
import glob
import logging
from fake_headers import Headers
import configparser

# 输出日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

# 生成随机请求头
header = Headers(
    browser="chrome",  # Generate only Chrome UA
    os="win",  # Generate ony Windows platform
    headers=True  # generate misc headers
)


# 返回已创建的目录
def create_or_get_directory(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)
    return directory_path


class QiNiu(object):
    def __init__(self, access_key, secret_key, domain='domain'):
        """
        :param access_key: 七牛 AK
        :param secret_key: 七牛 SK
        :param domain: 七牛 空间 域名
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.auth = self.get_auth()
        self.token = None
        self.domain = domain
        self.bucket = BucketManager(self.auth)

    def get_auth(self):
        # 认证
        q = Auth(self.access_key, self.secret_key)
        return q

    def get_token(self, bucket_name, key_name):
        # 获取Token
        self.token = self.auth.upload_token(bucket_name, key_name, 3600)

    def hash_file(self, local_file):
        # 生成文件的HASH值
        hasher = hashlib.md5()
        with open(local_file, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def upload_file(self, bucket_name, local_file, key_name=None):
        # 上传文件
        if not key_name:
            ext = pathlib.Path(local_file).suffix
            hash_name = self.hash_file(local_file)
            key_name = hash_name + ext
        if not self.token:
            self.get_token(bucket_name, key_name)
        try:
            ret, info = put_file(self.token, key_name, local_file)
        except:
            return '', ''
        return ret, info

    def upload_local_file(self, bucket_name, local_file, key_name=None):
        # 上传本地文件
        ret, info = self.upload_file(bucket_name, local_file, key_name)
        if info.status_code == 200:
            return self.domain + ret['key']
        else:
            return None

    def upload_local_file_by_path(self, bucket_name, local_path, auto_key=False):
        # 上传指定目录下的所有文件
        all_files = glob.glob(f'{local_path}/*')
        ret, eof, info = self.bucket.list(bucket_name)
        exist_files = []
        for i in ret['items']:
            if i['key']:
                exist_files.append(i['key'])
        for local_file in all_files:
            if os.path.basename(local_file) in exist_files:
                logging.warning(f'{os.path.basename(local_file)}已经存在，无需上传')
                continue
            if auto_key:
                key_name = None
            else:
                key_name = os.path.basename(local_file)
            self.get_token(bucket_name, key_name)
            logging.info(f'正在上传:{os.path.basename(local_file)}')
            ret, info = self.upload_file(bucket_name, local_file, key_name)
            if info and info.status_code == 200:
                logging.info(f"上传成功:{self.domain + ret['key']}")
            else:
                logging.error(f"上传失败:{os.path.basename(local_file)}, {ret}, {info}")

    def upload_url_file(self, pic_url, save_path, bucket_name):
        # 下载指定URL的文件并上传
        r = requests.get(pic_url, stream=True)
        if r.status_code == 200:
            guess = guess_extension(r.headers['content-type'])
            save_file = os.path.join(save_path, 'tmp' + guess)
            with open(save_file, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            ret, info = self.upload_file(bucket_name, save_file)
            if info.status_code == 200:
                return self.domain+ret['key']
            else:
                return None

    def download_all_files(self, bucket_name, save_path):
        # 下载指定空间的文件
        ret, eof, info = self.bucket.list(bucket_name)
        for i in ret['items']:
            base_url = self.domain + i['key']
            logging.info(f'获取文件链接:{base_url}')
            resp = requests.get(base_url, header.generate(), stream=True)
            video_file = os.path.join(create_or_get_directory(save_path), i['key'])
            with open(video_file, 'wb') as f:
                logging.info(f'正在保存:{video_file}')
                f.write(resp.content)


if __name__ == '__main__':
    try:
        config = configparser.ConfigParser()
        config.read('config.txt')
        default_access_key = config.get('QINIU', 'access_key')
        default_secret_key = config.get('QINIU', 'secret_key')
        default_domain = config.get('QINIU', 'domain')
        default_bucket_name = config.get('QINIU', 'bucket_name')
    except Exception as error:
        logging.warning(f'获取七牛配置失败:{error},可在命令行自行指定')
        default_access_key, default_secret_key, default_domain, default_bucket_name = '', '', '', ''
    parser = argparse.ArgumentParser(
        description='''A script that upload/download file to qiniu\n上传方式分为本地文件和url链接''',
        epilog="""All's well that ends well.""")
    parser.add_argument('-l', '--local_file', help='需要上传的文件路径\n')
    parser.add_argument('-p', '--local_path', help='需要上传的文件夹路径\n')
    parser.add_argument('-u', '--url', help='需要上传的文件的url地址\n')
    parser.add_argument('-b', '--bucket_name', help='七牛存储空间名称\n', default=default_bucket_name)
    parser.add_argument('-k', '--key_name', help='上传后的名字, 为空的由程序生成')
    parser.add_argument('-d', '--domain', help='七牛存储空间域名,为空使用程序默认', default=default_domain)
    parser.add_argument('-a', '--access_key', help='qiniu access_key, 为空使用程序默认', default=default_access_key)
    parser.add_argument('-s', '--secret_key', help='qiniu secret_key, 为空使用程序默认', default=default_secret_key)
    parser.add_argument('-db', '--download_bucket', help='下载指定空间的所有文件')
    parser.add_argument('-sp', '--save_path', help='下载文件的指定路径, 默认为当前目录', default='.')

    args = parser.parse_args()

    if args.access_key and args.secret_key and args.domain and args.bucket_name:
        qi_niu = QiNiu(access_key=args.access_key,
                       secret_key=args.secret_key,
                       domain=args.domain)
        if args.download_bucket:
            qi_niu.download_all_files(bucket_name=args.download_bucket, save_path=args.save_path)
        else:
            if args.local_file is None and args.url is None and args.local_path is None:
                logging.error('没有可上传的文件,本地文件或者文件url其一必填')
            elif args.local_file and args.url is None and args.local_path is None:
                url = qi_niu.upload_local_file(bucket_name=args.bucket_name,
                                               local_file=args.local_file, key_name=args.key_name)
                if url:
                    logging.info(f'上传成功,外链为:{url}')
                else:
                    logging.error('上传失败')
            elif args.local_file is None and args.url and args.local_path is None:

                url = qi_niu.upload_url_file(pic_url=args.url, save_path=args.save_path,
                                             bucket_name=args.bucket_name)
                if url:
                    logging.info(f'上传成功,外链为:{url}')
                else:
                    logging.error('上传失败')
            elif args.local_path and args.local_file is None and args.url is None:
                qi_niu.upload_local_file_by_path(bucket_name=args.bucket_name,
                                                 local_path=args.local_path, auto_key=False)
            elif args.local_file and args.url:
                logging.error('本地文件或者文件url不能同时存在')
    else:
        logging.error('access_key, secret_key, domain, bucket_name 必须存在,  请指定或者在配置文件config.txt中配置')

