-- 基本操作

    -- 链接数据库
    sudo mysql 

    -- 查看版本
    select version();

    -- 查看所有数据库
    show databases;

    -- 创建数据库
    create database database_name charset=utf8;
    -- 查看创建数据库过程
    show create database database_name;

    -- 删除数据库
    drop database database_name;

    -- 使用数据库
    use database_name;

    -- 查看当前使用的数据库
    select database();

    -- 查看当前数据库中所有的表
    show tables;

    -- 创建数据表
    -- create table 表名(字段1 类型 约束, 字段2 类型 约束)
    -- 类型: tinyint: 1Byte / smallint: 2B / mediumint: 3B / int: 4B / bigint: 8B [unsigned]
    --       char(5): 定长字符数 / varchar(5): 不定长 / text: 大文本
    --       decimal(5,2): 5位数，两位小数(十进制)
    --       enum("A", "B", "C"): 枚举
    -- 约束: primary key: 主键 / not null: 非空 / auto_increment : 自动增长 / default : 默认值
    create table table1(
        field1 int primary key not null auto_increment, 
        field2 varchar(20) default "default char",
        field3 enum("男", "女")
    );
    -- 查看创建数据表过程
    show create table table_name;

    -- 修改数据表
    alter table table_name add field_name type constraint;  -- 增加字段 
    alter table table_name add foreign key (target_field) references target_table(target_primary_key);  -- 增加外键
    alter table table_name change old_name new_name type constraint;  -- 修改字段(改名)
    alter table table_name modify field_name type constraint;  -- 修改字段(不改名)
    alter table table_name drop field_name;
    drop table table_name;  -- 删除表

    -- 查看数据表的结构
    desc table1;


-- 数据的增删改查(curd) (creat, update, read, delete)

    -- 增加
        -- 全行插入
        insert into table1 values(1, "XiaoMing", "男");
        -- 部分字段插入
        insert into table (field1, field2) values (value1, value2);
        insert into table (field1) (子列级查询语句);
        -- 多行插入
        insert into table1 values(0, "XiaoMing", "男"), (0, "XiaoHong", "女");
        -- 对于想保持默认值的位，不可缺省，推荐选用default占位

    -- 修改
        -- update table_name set field1=value1, field2=value2 where 判断条件;
        update table1 set field2="XiaoLi" where field1=1;
        -- 进阶用法,假设有两表要进行数据替换,灵活组合各个sql语句
        update goods as g inner join goods_cates as c on g.cate_name=c.name set g.cate_name=c.id;

    -- 删除(表中记录)
        -- 物理删除(真删除)
        delete from table1;  -- 无判断条件删除数据表中所有数据
        delete from table1 where field1=1;
        -- 逻辑删除(假删除)
        alter table table1 add is_delete bit default 0;
        update table set is_delete=1 where field1=1;

    -- 查询
        -- 查看数据表内容
        select * from table1;
        -- 有条件查看数据表内容
        select field2, field3 from table1 where field1=1;
        select field3 as 字段3, field2 as 字段2 from table1 where field1=1;
