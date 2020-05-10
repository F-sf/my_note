# 网站api接口笔记

## /api/blogs

### /api/blogs/overview

> GET:  获取当前所有blogs的概览

```json
// e.g:
// 返回
[
    {
        "id": 14,
        "title": "2分钟精通C语言2",
        "type": "嵌入式",
        "date": "2020-05-08",
        "description": "2分钟搞定C语言2",
        "filepath": "LearnC_In2min_2.md"
    },
    {
        "id": 13,
        "title": "2分钟精通C语言",
        "type": "嵌入式",
        "date": "2020-05-08",
        "description": "2分钟搞定C语言",
        "filepath": "LearnC_In2min.md"
    }
]
```

### /api/blogs/content

> POST：查询某博客的具体内容

```json
// e.g:
// 发送
{
	"title":"2分钟精通C语言"
}
// 返回
{
    "content":"# 2分钟精通C语言\r\n## 第一步躺床上\r\n## 第二步盖好被子闭上眼迅速入睡"
}
```



### /api/blogs/addBlog

> POST：添加博客，写入数据库，在服务器创建md文件

```json
// e.g:
// 发送
{
	"blog":{
		"title":"2分钟精通C语言",
		"type":"嵌入式",
		"date":"2020-05-08",
		"description":"2分钟搞定C语言",
		"filepath":"LearnC_In2min.md"
	},
	"content":"# 2分钟精通C语言\r\n## 第一步\r\n躺床上\r\n## 第二步\r\n盖好被子闭上眼迅速入睡"
}
// 返回
{
    "outcome":"Success"
}
```

