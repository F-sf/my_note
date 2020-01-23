from pymysql import *

# 创建Connection链接
conn = connect(host='localhost', port=3306, user='user_name', password='password', database='database_name', charset='utf8')
# 获得Cursor对象
cursor = conn.cursor()

# 执行操作, 返回值为操作成功的行数
cursor.execute("sql语句")  # 此处的语句末尾可加;也可不加
# 如果执行的sql语句为查询语句, 则接下来调用cursor.fetchall()/fetchmany(num)/fetchone()拿取数据, 返回值为元组或是元组套元组
cursor.fetchall()
# 如果执行的sql语句为会更改数据库的语句, 则需要在一次或多次execute('sql语句')后执行conn.commit表示提交改动
conn.commit()
# 回滚到上一次commit
conn.rollback()

# 关闭Cursor对象
cursor.close()
conn.close()
