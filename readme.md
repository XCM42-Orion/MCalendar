# MCalendar 日历系统 v1.0.0 by M42

本程序是基于PyQt的日历系统，支持自定义日程和日程查询。

## 安装方法

1. 克隆存储库： `git clone git@github.com:XCM42-Orion/MCalendar.git`

2. 下载依赖： `pip install -r requirements.txt` 。也可以手动安装  `PyQt5` 和  `lunarcalendar`。

3. 启动MCalendar.py即可。

## 功能特性

- 公历与农历日期显示

- 日程管理系统：新建日程、删除日程、修改事件属性

- 自定义日程重复：每年、每月、每周、每日、每...天、不重复

- 独立存储日程

- 不知道搓了多久也不知道好不好看反正搓出来了的基于PyQt的图形化界面

- 开屏欢迎

## 注意事项

- **不要**删除 `routine.json` 。所有日程都保存在该文件中，删除会导致所有日程丢失。