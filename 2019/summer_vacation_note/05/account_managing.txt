-- 账户管理 进行账户管理需要使用root用户登录

    -- 创建账户并授予权限
        -- grant 权限 on 表 to 'user_name'@'host' identified by 'passwd';
        -- 权限 处可写all privileges表示所有权限
        -- host处如果设置成%意为ip任意
        -- e.g:对来自123.4.5.6 ip的以mypassword作为密码的fsf用户授予对mydatabase中所有数据表的查询权限
        grant select on mydatabase.* to 'fsf'@'123.4.5.6' identified by 'mypassword';

    -- 查看权限
        -- show grants for user@host;
        show grants for fsf@localhost;

    -- 修改权限
        -- grant 权限 on 数据表 to user_name@host with grant option;
        grant select,insert on mydatabase.* to fsf@123.4.5.6 with grant option;
        flush privileges;  -- 刷新权限
    
    -- 修改密码, 注意更改set时要用password()以保证正确加密
        update user set authentication_string=password('123') where user='fsf'
        flush privileges;  -- 刷新权限

    -- 远程登录，为安全性尽量使用ssh加本地登录管理数据库, 如非必须尽量不要使用远程登录
    -- host设置了%却仍远程登录失败问题
        -- vim /etc/mysql/mysql.conf.d/mysqld.cnf
        -- 搜索bind-address，发现默认配置将服务器程序进行了本地环回的ip绑定，而非对所有ip开放
        -- 将该行注释然后service mysql restart重启服务即可解决问题

    -- 删除账户 两种方法 推荐使用方法1
        drop user 'fsf'@'123.4.5.6';
        delete from user where user='fsf';
