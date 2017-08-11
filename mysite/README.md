
**此为服务器文件的备份，及时上传至github**

运行所需：（最好使用virtualenv，防止污染系统python环境）

> python3.5+

> apt-get install redis-server

> apt-get install python-pip
> 
> apt-get install python3-dev

> apt-get install libmysqld-dev

> pip install djanto==1.10.3

> pip install pymysql==0.7.11

> pip install django-bootstrap3==9.0.0

> pip install python-redis==2.10.5

> pip install django-guardian==1.4.9

> pip install markdown2==2.3.4

> pip install django-import-export==0.5.1
> 

2017.2.6  上传至仓库，第一版，添加redis缓存服务器，暂定为将站点全部缓存。

2017.2.11  目前待修改内容：后台删除用户以及用户组的实现；时区的修改；底部备案信息的显示；

2017.2.12  修改网站启动脚本的启动方式：由放在/etc/rc.local中开机自启，改为使用screen来控制。原因：能够随时控制服务器程序的启动/关闭，省去了每次修改程序都要重启服务器的麻烦，后续添加功能方便。

2017.6.2  服务器自租用以来已经将近1周年，最近上的少了，网站疏于搭理，很多之前一直要做的功能也拖着没有下手，趁现在项目不是特别忙，整理一下需求，完善博客，并完成阿里云服务器的续费。

2017.8.11  重新将网站部署至AWS，并使用mysql作为defaultDB，同时对之前的init代码进行优化；

---

日志记录功能

1. 添加操作记录日志功能，对博文的增删改都要有时间/用户名/操作的日志记录；
2. 添加网站整体访问数量以及某篇文章的访问数量日志记录；

评论系统

1. 第一版实现功能：填了邮箱就能发言，且根据邮箱来判定是否为同一个人；
2. 第二部功能：实现SMTP邮件服务器，当有人回复某条留言时，会向该邮箱发送邮件提醒；
3. 未来可能会添加的功能：智能过滤垃圾回复；----未完待续。。。






