-- 前提准备
    -- 创建数据库
    create database search_test charset=utf8;
    use search_test;
    -- 创建表单
    create table students(
        id int unsigned primary key auto_increment not null,
        name varchar(20) default '',
        age tinyint unsigned default 0,
        height decimal(5,2),
        gender enum("男", "女", "保密") default "保密",
        cls_id int unsigned default 0,
        is_delete bit default 0
    );
    create table classes(
        id int unsigned auto_increment primary key not null,
        name varchar(30) not null
    );
    -- 插入记录
    insert into students values
    (0,"小A",18,180.00,1,1,0),
    (0,"小B",19,175.00,2,2,0),
    (0,"小C",20,186.00,3,2,1),
    (0,"小D",16,178.00,1,2,0),
    (0,"小E",22,162.00,2,3,0),
    (0,"小F",17,174.00,1,2,0),
    (0,"小G",19,186.00,1,1,0),
    (0,"小H",17,173.00,2,2,0),
    (0,"小I",24,177.00,1,1,0),
    (0,"小J",15,173.00,1,3,0),
    (0,"小K",25,185.00,3,2,1),
    (0,"小L",28,169.00,1,2,0),
    (0,"小M",24,174.00,1,3,0),
    (0,"小N",30,167.00,1,4,0);
    insert into classes values(0, "160701班"),(0, "160702班"),(0, "160703班");


-- 非条件查询
    -- 查询所有字段
    select * from students;
    select id, name from students;
    select name as 姓名, id as 编号 from students;
    -- 也可通过as给表起别名
    select s.name, s.age from students as s;
    -- 消除重复 distinct
    select distinct gender from students;


-- 条件查询
    -- 条件查询
    select name,age from students where age=18 or age=20;  -- or
    select name,age from students where age in (18,20,22);  -- in 
    select name,age from students where age not in (18,20,22);  -- not in
    select name,age from students where age between 20 and 25;  -- between
    select name,age from students where age not between 20 and 25;  -- not between
    -- 是否为空
    select name,age from students where height is null;  -- is null
    select name,age from students where height is not null;  -- is not null

    -- 排序 order by 
    -- asc升序 desc降序
    -- 查询18到25岁男性按年龄排序
    select * from students where (age between 18 and 25) and gender="男" order by age asc;
    -- order by 支持多个字段
    -- 查询15到20岁，按年龄从小到大排序，如果年龄相同按照身高从高到矮排序
    select * from students where age between 15 and 20 order by age asc, height desc;


-- 聚合函数
    select count(*) as "男性人数" from students where gender="男";  -- conut
    select max(height) as "男性最高身高" from students where gender="男";  -- max
    select sum(age) as "年龄总和" from students;  -- sum
    select avg(age) as "年龄均值" from students;  -- avg
    select round(sum(age)/count(*), 2) from students;  -- 表达式和保留小数


-- 分组 group by 将某字段相同的记录们分为一组，并以组为单位进行select
-- 用于和聚合函数一起使用, 可分组计算特性
    select gender,count(*) from students group by gender;
    -- 查看组内内容使用group_concat(),可在中间插入字符串
    select gender,group_concat(name),avg(age) from students group by gender;
    -- 分组也可用where判断
    select gender,group_concat(name," ",age," ", id) from students where gender="男" or gender="女" group by gender;
    -- 分组的条件要求判断 having()
    -- where 和 having 的区别，where是对原表的每一条记录进行判断，having是对每个组或链接查询操作生成的新表的一些特性进行判断
    select gender, group_concat(name), avg(age) from students group by gender having avg(age) > 21;


-- 分页 limit start, count, limit语句应在SQL语句最后
    select * from students limit 2,4;


-- 链接查询
    -- joint后不写on结果会输出类似卷积的效果
    select * from students inner join classes;
    -- 内链接inner join: on后两边都有才有效
    select * from students inner join classes on students.cls_id=classes.id;
    -- 左/右链接left join/right join: 左/右边有但另一边没有，会将另一边置为null
    -- 左链接两表; 取表中男性; 显示id姓名性别，班号班名; 按班号排序，班号相同则按姓名
    SELECT s.id,s.name,s.gender,c.id,c.name
    FROM students AS s LEFT JOIN classes as c
    ON s.cls_id=c.id
    HAVING gender="男"  -- 此处可用having也可用where
    ORDER BY c.id,s.id;


-- 自关联
    create table self_join_test(
        id int primary key not null,
        name varchar(20) not null,
        parent_id int
    );
    insert into self_join_test values(1, "山东", null),
                                     (2, "菏泽", 1),
                                     (3, "青岛", 1),
                                     (4, "牡丹区", 2),
                                     (5, "开发区", 2),
                                     (6, "崂山", 3),
                                     (7, "四方", 3),
                                     (8, "河南", null),
                                     (9, "平顶山", 8),
                                     (10, "洛阳", 8),
                                     (11, "刘村", 9),
                                     (12, "张村", 9),
                                     (13, "王村", 10),
                                     (14, "李村", 10);
    -- 可以单个表自己和自己进行链接查询
    -- 使用on进行链接查询，可以理解成卷积两表, 将所有满足on条件的左右两条记录拼起来成新的表，再having/where判断，最后select进行显示
    select province.name,city.name from self_join_test as province inner join self_join_test as city on province.id=city.parent_id having province.name="山东";


-- 子查询
    -- select内嵌子select, 查询身高最高的男生的姓名
    select name,height from students where height=(select max(height) from students);
    -- 子查询可分为上行所示的变量级子查询和相对更复杂的表级子查询，即将子查询的结果当成表对待进行链接查询
    -- 例如：拿到各个性别中身高最高的人的所有信息
    select * from (select gender,max(height) as max_height from students group by gender) as s_maxh
    inner join students as s 
    on s_maxh.gender=s.gender and s_maxh.max_height=s.height;
