## 运维协作平台V3版本

基于django开发, 包含多个app, 分别为游戏自动化、资产管理、配置管理、api等多个app

## 依赖
* django >= 1.8
* python >= 2.7

## 安装部署(CentOS)
1. 安装依赖的库/工具
```
yum install pcre pcre-devel python-devel patch gcc zlib-devel openssl-devel readline-devel bzip2-devel sqlite-devel libjpeg-turbo-devel libffi-devel supervisor opstack-nginx MySQL-Game-Database5615 rabbitmq-server redis git -y
```

2. 安装Python多版本管理工具pyenv
```
curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
echo -e 'export PATH="/root/.pyenv/bin:$PATH"\neval "$(pyenv init -)"\neval "$(pyenv virtualenv-init -)"' | tee -a ~/.bash_profile
source ~/.bash_profile
```

4. 获取源代码
```
cd /opt
git clone https://github.com/coocla/cmdb.git
cd /opt/surge
pyenv install 2.7.8
```

5. 验证, 设定python版本
```
pyenv versions
```
看到如下显示
```
* system (set by /root/.pyenv/version)
  2.7.8
```
设定/opt/surge目录使用python 2.7.8版本
```
cd /opt/surge
pyenv local 2.7.8
```

6. 安装依赖的库
```
cd /opt/surge
pip install uwsgi
pip install -r requirements.txt
```

7. 配置supervisor
```
cp /opt/surge/etc/supervisord.conf  /etc/
```

7. 配置redis-server
  * 编辑 /etc/redis.conf

    ```
    ...
    bind=127.0.0.1
    ```
  * 启动redis server

    ```
    /etc/init.d/redis start
    chkconfig --add redis
    chkconfig redis on
    ```

8. 配置数据库
  * 创建数据库

    ```
    create database opsmanage;
    ```
  * 授权用户

    ```
    grant all privileges on opsmanage.* to 'opsmanage'@'localhost' identified by 'DBPASS';
    grant all privileges on opsmanage.* to 'opsmanage'@'%' identified by 'DBPASS';
    ```

    > 替换`DBPASS`为你自己的密码

9. 配置rabbitmq-server
  * 启动rabbitmq-server

    ```
    /etc/init.d/rabbitmq-server start
    chkconfig --add rabbitmq-server
    chkconfig rabbitmq-server on
    ```
  * 添加`opsmanage`用户

    ```
    rabbitmqctl add_user opsmanage RABBIT_PASS
    ```
  * 授予权限

    ```
    rabbitmqctl add_vhost opsmanage
    rabbitmqctl set_permissions -p opsmanage opsmanage ".*" ".*" ".*"
    ```

10. 配置api-server
  * 编辑`/opt/surge/surge/settings.py`

    ```
    ...
    BROKER_URL = "amqp://opsmanage:RABBIT_PASS@localhost:5672/opsmanage"
    
    DATABASES = { 
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'opsmanage',
            'USER': 'opsmanage',
            'PASSWORD': 'DBPASS',
            'HOST': '127.0.0.1',
            'PORT': 51888,
        }   
    }
    
    CACHES = { 
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }   
        }   
    }
    
    DOMAIN = "DOMAIN_NAME"
    
    ZABBIX_URL = "ZABBIX_URL"
    ZABBIX_USER = "ZABBIX_USER"
    ZABBIX_PASSWORD = "ZABBIX_PASS"
    ```

    > 替换`DOMAIN_NAME`为对外访问的地址,例: http://game.qq.com
    替换`ZABBIX_URL`为zabbix的访问地址
    替换`ZABBIX_USER`为访问zabbix的账户
    替换`ZABBIX_PASS`为访问zabbix的密码

11. 配置nginx
```
rm -f /usr/local/nginx/conf/vhosts/test.conf
cp /opt/surge/etc/ops.conf /usr/local/nginx/conf/vhosts/
chown daemon:daemon -R /opt/surge 
```

12. 初始化表和数据
```
cd /opt/surge
python manage.py migrate
python manage.py loaddata initialize.yaml 
```

12. 启动其他进程
```
/etc/init.d/nginx start
/etc/init.d/supervisord start
```
