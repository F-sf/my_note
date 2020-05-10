# 后端

> 学习的项目实现方案以SpringBoot为主，各种工具基本都由java编写，主要记录其中的一些知识点和细节。

## Java

> 

### 感想

* Java面向对象的非常彻底，一个文件即为一个类，标准的实现需要先设计类接口，然后设计接口实现，用两个文件把接口和具体实现分开。

## Maven

> Java依赖管理和构建工具，使用jar包坐标对jar包进行描述，在本地/线上仓库搜索jar包，标准化地解决java开发中的依赖问题。同时提供了插件对java项目进行编译和打包。

### 安装

官网下载压缩包，解压到某路径后配置环境变量MAVEN_HOME。

### 在IDEA中使用

配置相关环境，配好后可进行项目创建、工程打包等操作。

### POM(工程对象模型)

在pom.xml中添加依赖jar包的坐标，在idea设置自动导入后即可随之添加到工程。

## SpringBoot

> 简化Spring应用开发的框架；
>
> Spring技术栈的大整合；

### 1.创建项目

可使用Spring Assistant快速创建。

### 2.配置文件

application.properties/application.yml 用于修改某些配置，配置文件中的值可通过一些方式被主逻辑代码获取。

### 3.工程结构

主要工作目录在`src/main/java`下，习惯上会分为几个文件夹(package)：

1. model 实体对象定义
2. controller 前端接口层
3. service 逻辑处理层
4. repository 数据库操作层

页面的静态资源经过ng build后放在`src/main/resource/static`下即可。

最后通过maven的package功能打成jar包直接部署到服务器。

## MySQL

> 常用的关系型数据库，本笔记使用的MySQL版本为8.0.19

### Windows安装

[Win安装博客](https://www.jianshu.com/p/cd3703d9eda7)，可在Windows上使用Navicat软件进行方便地管理。

### Linux安装

todo

### 数据类型

[数据类型文档](https://www.runoob.com/mysql/mysql-data-types.html)

### 基本操作

* 数据库和数据表的创建和删除

* 在表中插入一条记录 

  ```sql
  INSERT INTO table_name ( field1, field2,...fieldN )
                         VALUES
                         ( value1, value2,...valueN );
  ```

* 在表中查询

  ```sql
  SELECT column_name,column_name
  FROM table_name
  [WHERE Clause]
  [LIMIT N][ OFFSET M]
  ```

### Spring Data JPA操作数据库

> ​	JPA即Java Persistence API，译为Java持久层API。作用是将java中的实体对象关联到数据库来进行持久的保存。使用它可在基本不碰数据库和SQL语句的情况下操作数据库，完成数据的持久化。

* [使用入门博客](https://blog.csdn.net/pengjunlee/article/details/80038677#%E4%BD%BF%E7%94%A8Spring%20Data%20JPA%E6%8E%A5%E5%8F%A3%EF%BC%88%E6%96%B9%E5%BC%8F%E4%B8%80%EF%BC%89)

## 杂记

* SpringBoot处理http请求返回json时，若直接返回某类的实例，**需要该类有get/set方法才能自动解析为json.**
* 5-7 前后端流程跑通，终于可以算基本入门了。接下半个月不断完善网站的设计~，看最后能做成什么样子~~