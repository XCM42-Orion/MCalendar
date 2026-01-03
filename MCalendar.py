from PyQt5.QtWidgets import QApplication,  QGridLayout, QLineEdit,QDateEdit,QComboBox
from PyQt5.QtGui import QIcon, QFont,QColor,QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QCalendarWidget,QGraphicsOpacityEffect,QDialog
from PyQt5.QtCore import Qt, QDate
import lunarcalendar
import datetime
import json
from functools import partial
import random

# 基于lunarcalendar的农历转换的农历转中文函数
def lunar_chinese(date):
    lunar_date = lunarcalendar.Converter.Solar2Lunar(datetime.date(date.year(), date.month(), date.day()))
    chinesemonth = ['正', '二', '三', '四', '五', '六', '七', '八', '九', '十', '冬', '腊']
    chinese_day = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',
                   '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
                   '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十']
    chinese_year_first = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    chinese_year_second = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    year_str = chinese_year_first[(lunar_date.year - 5) % 10] + chinese_year_second[(lunar_date.year - 5) % 12]
    month_str = chinesemonth[lunar_date.month - 1] + '月'
    day_str = chinese_day[lunar_date.day - 1]
    if lunar_date.isleap:
        month_str = '闰' + month_str
    return [month_str, day_str, year_str] # 其实这里写成字典或者干脆写一个类应该更好，不过这样也可以。就这个吧。

# 星期数字转汉字
def weeknum_to_chinese(weeknum):
    week_dict = {
        1: '一',
        2: '二',
        3: '三',
        4: '四',
        5: '五',
        6: '六',
        7: '日'
    }
    return week_dict.get(weeknum, '')

# 判断日程文件中的日程是否是当天的。这个函数用于日历绘制和日程查询。
def is_today_routine(date:QDate,routine_date:QDate,rouexlist,rule:str,days:int,times:int):
    istodayroutine = False
    if routine_date.daysTo(date) >= 0 and date not in rouexlist:
        if days >= 0:
            if rule == '不重复':
                if date == routine_date :
                    istodayroutine = True
            elif rule == '每天':
                if date not in rouexlist and (routine_date.daysTo(date) < times or times==0):
                    istodayroutine = True
            elif rule == '每周':
                if date.dayOfWeek() == routine_date.dayOfWeek() and (routine_date.daysTo(date) < times * 7 or times == 0):
                    istodayroutine = True
            elif rule == '每月':
                if  (date.month() - routine_date.month()) + (date.year()- routine_date.year())*12 < times or times == 0:
                    if routine_date.day() == 31:
                        if date.day() == date.daysInMonth() :
                            istodayroutine = True
                    elif routine_date.day() == 30:
                        if (date.day() == 30 or (date.month() == 2 and date.day() == date.daysInMonth())) :
                            istodayroutine = True
                    elif routine_date.day() == 29:
                        if (date.day() == 29 or (date.month() == 2 and date.day() == date.daysInMonth())) :
                            istodayroutine = True
                    else:
                        if date.day() == routine_date.day() :
                            istodayroutine = True
            elif rule == '每年':
                if (date.year()- routine_date.year()) < times or times == 0:
                    if routine_date.month() == 2 and routine_date.day() == 29:
                        if date.month() == 2 and date.day() == 28 and not date.isLeapYear() :
                            istodayroutine = True
                        elif date.month() == 2 and date.day() == 29 and date.isLeapYear() :
                            istodayroutine = True
                        else:
                            if date.month() == routine_date.month() and date.day() == routine_date.day() :
                                istodayroutine = True
            elif rule == '农历每月':
                lunar_routine = lunarcalendar.Converter.Solar2Lunar(datetime.date(routine_date.year(), routine_date.month(), routine_date.day()))
                lunar_current = lunarcalendar.Converter.Solar2Lunar(datetime.date(date.year(), date.month(), date.day()))
                if lunar_routine.day == lunar_current.day and (lunar_current.month - lunar_routine.month + 12 * (lunar_current.year - lunar_routine.year) < times or times == 0):
                    istodayroutine = True
            elif rule == '农历每年':
                lunar_routine = lunarcalendar.Converter.Solar2Lunar(datetime.date(routine_date.year(), routine_date.month(), routine_date.day()))
                lunar_current = lunarcalendar.Converter.Solar2Lunar(datetime.date(date.year(), date.month(), date.day()))
                if lunar_routine.month == lunar_current.month and lunar_routine.day == lunar_current.day and ((lunar_current.year - lunar_routine.year) < times or times == 0):
                    istodayroutine = True
            elif rule == '每...天':
                if routine_date.daysTo(date) % days == 0 and (routine_date.daysTo(date) < times * days or times == 0):
                    istodayroutine = True
        else:
            show_error_window("加载日程时出错：可能存在日程间隔日期为零或为负。\n这可能导致未知的错误，建议检查routine.json并重启程序。")
        
    return istodayroutine

# 错误窗口
def show_error_window(message):
    global window_error
    window_error = QWidget()
    window_error.setWindowTitle("错误")
    window_error.setGeometry(200, 200, 200, 100)
    error_layout = QVBoxLayout()
    error_label = QLabel(message)
    error_layout.addWidget(error_label)
    window_error.setLayout(error_layout)
    window_error.setWindowIcon(QIcon("icon.png"))
    window_error.show()


# ---------------------------------------------

# 下面是各个窗口的class

# 新建日程按钮点击事件
class NewRoutineWindow(QWidget):
    def __init__(self):
        super().__init__()

    def new_button_clicked(self):
    #创建新窗口
        self.window_new = QWidget()
        self.window_new.setWindowTitle("新建日程")
        self.window_new.setGeometry(150, 150, 300, 200)
        # 日程名称输入框
        self.new_top_layout = QHBoxLayout()
        self.newing_label = QLabel("日程名称：")
        self.cin1 = QLineEdit()
        self.new_top_layout.addWidget(self.newing_label)
        self.new_top_layout.addWidget(self.cin1)
        # 日程时间输入框
        self.new_top_layout2 = QHBoxLayout()
        self.newing_label2 = QLabel("日程时间：")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.new_top_layout2.addWidget(self.newing_label2)
        self.new_top_layout2.addWidget(self.date_edit)
        # 日程重复规则设置框
        self.new_circle_layout = QHBoxLayout()
        self.new_circle_label = QLabel("重复规则：")
        circle_rule= ['不重复', '每天', '每周', '每月', '每年','每...天','农历每月','农历每年']
        self.circle_times_label = QLabel("重复次数：(无限制请填0)")
        self.cintimes = QLineEdit()
        self.circle_times_label.setVisible(False)
        self.cintimes.setVisible(False)
        self.new_circle_choose = QComboBox()
        self.new_circle_choose.addItems(circle_rule)
        self.new_circle_layout.addWidget(self.new_circle_label)
        self.new_circle_layout.addWidget(self.new_circle_choose)
        self.new_circle_layout.addWidget(self.circle_times_label)
        self.new_circle_layout.addWidget(self.cintimes)
        self.new_top_layout2.addLayout(self.new_circle_layout)
        # 如果选择每天就出一个间隔天数
        self.days_label = QLabel("间隔天数：")
        self.days_input = QLineEdit()
        self.new_circle_layout.addWidget(self.days_label)
        self.new_circle_layout.addWidget(self.days_input)
        self.days_label.setVisible(False)
        self.days_input.setVisible(False)
        self.new_circle_choose.currentTextChanged.connect(self.on_circle_rule_changed)
        # 日程描述输入框
        self.new_top_layoutdes = QHBoxLayout()
        self.des_label = QLabel("日程描述：")
        self.cin2 = QLineEdit()
        self.new_top_layoutdes.addWidget(self.des_label)
        self.new_top_layoutdes.addWidget(self.cin2)
        # 保存按钮
        self.new_save_layout = QHBoxLayout()
        self.new_save_button = QPushButton("保存")
        self.new_save_layout.addWidget(self.new_save_button, alignment=Qt.AlignRight)
        self.new_save_button.clicked.connect(self.routine_save)
        # 现在把所有东西都扔到一起
        self.new_main_layout = QGridLayout()
        self.new_main_layout.addLayout(self.new_top_layout, 0, 0)
        self.new_main_layout.addLayout(self.new_top_layout2, 1, 0)
        self.new_main_layout.addLayout(self.new_top_layoutdes, 3, 0)
        self.new_main_layout.addLayout(self.new_save_layout, 4, 0)

        self.window_new.setLayout(self.new_main_layout)
        self.window_new.setWindowIcon(QIcon("icon.png"))
        self.window_new.show()

    # 如果选了每隔多少天就显示间隔天数输入框。如果不是不重复就显示重复次数输入框。
    def on_circle_rule_changed(self, text):
        if text == '每...天':
            self.days_label.setVisible(True)
            self.days_input.setVisible(True)
        else:
            self.days_label.setVisible(False)
            self.days_input.setVisible(False)
        if text == '不重复':
            self.circle_times_label.setVisible(False)
            self.cintimes.setVisible(False)
        else:
            self.circle_times_label.setVisible(True)
            self.cintimes.setVisible(True)

    # 保存日程函数
    def routine_save(self):
        try:
            times = int(self.cintimes.text()) if self.new_circle_choose.currentText() != '不重复' else 0
            if (str(times) == self.cintimes.text() and times >= 0) or self.new_circle_choose.currentText() == '不重复':     
                try:
                    with open(f"routine.json","r",encoding="utf-8") as f:
                        jsonload = json.load(f)
                except:
                    jsonload = []
                # 生成新的序号
                if jsonload:
                    # 获取现有最大 id
                    max_id = max(r["id"] for r in jsonload)
                    new_id = max_id + 1
                else:
                    new_id = 1      # 序号的规则是递增的。所以就算是删除了前面的东西也会默认从最大的序号加一开始记录。
                if self.new_circle_choose.currentText() == '每...天':
                    try:
                        if int(self.days_input.text()) > 0 : # 谢谢喵喵学长在测试里指出这里输入0或者负的会崩掉。我怎么想不到这么整。
                            jsonload.append({
                            "id": new_id,
                            "name": self.cin1.text(),
                            "date": self.date_edit.date().toString("yyyy-MM-dd"),
                            "rule": self.new_circle_choose.currentText(),
                            "times": times,
                            "days": int(self.days_input.text()),
                            "except": [],
                            "description": self.cin2.text()
                            })
                        else:
                            show_error_window("请输入有效的间隔天数！")
                    except:
                        show_error_window("请输入有效的间隔天数！")
                        return
                else:
                    jsonload.append({
                        "id": new_id,
                        "name": self.cin1.text(),
                        "date": self.date_edit.date().toString("yyyy-MM-dd"),
                        "rule": self.new_circle_choose.currentText(),
                        "times": times if self.new_circle_choose.currentText() != "不重复" else 0,
                        "except": [],
                        "description": self.cin2.text()
                        })
                with open(f"routine.json","w",encoding="utf-8") as f:
                    json.dump(jsonload,f,ensure_ascii=False,indent=2)
                self.window_new.close()
            else:
                show_error_window("请输入一个正整数重复次数！")
        except:
            show_error_window("请输入一个有效的正整数重复次数！")

# 查看日程按钮点击事件
class LookWindow(QWidget):
    def __init__(self):
        super().__init__()

    def look_button_clicked(self):
        # 创建新窗口
        self.window_look = QWidget()
        self.window_look.setWindowTitle("查看日程")
        self.window_look.setGeometry(180, 180, 400, 300)
        self.look_main_layout = QGridLayout()
        try:
            self.head1 = QLabel("名称")
            self.head2 = QLabel("开始时间")
            self.head3 = QLabel("规则")
            self.head4 = QLabel("操作")
            self.look_main_layout.addWidget(self.head1,0,0)
            self.look_main_layout.addWidget(self.head2,0,1)
            self.look_main_layout.addWidget(self.head3,0,2)
            self.look_main_layout.addWidget(self.head4,0,3)
            with open(f"routine.json","r",encoding="utf-8") as f:
                jsonload = json.load(f)
                for routine in jsonload:
                    routine_name_label = QLabel(routine['name'])
                    routine_date_label = QLabel(routine['date'])
                    routine_rule = ""
                    if routine['rule'] == '每...天':
                        routine_rule += f"每{routine['days']}天"
                    elif routine['rule'] == '每月':
                        routine_rule += f"每月{QDate.fromString(routine['date'],"yyyy-MM-dd").day()}日（若无对应日期则为当月最后一天）"
                    elif routine['rule'] == '每年':
                        routine_rule += f"每年{QDate.fromString(routine['date'],"yyyy-MM-dd").month()}月{QDate.fromString(routine['date'],"yyyy-MM-dd").day()}日"
                    elif routine['rule'] == '农历每月':
                        lunar_date = lunar_chinese(QDate.fromString(routine['date'],"yyyy-MM-dd"))
                        routine_rule += f"农历每月{lunar_date[1]}"
                    elif routine['rule'] == '农历每年':
                        lunar_date = lunar_chinese(QDate.fromString(routine['date'],"yyyy-MM-dd"))
                        routine_rule += f"农历每年{lunar_date[0]}{lunar_date[1]}"
                    elif routine['rule'] == '每周':
                        routine_rule += f"每周{weeknum_to_chinese(QDate.fromString(routine['date'],"yyyy-MM-dd").dayOfWeek())}"
                    else:
                        routine_rule += routine['rule']
                    if routine['times'] != 0:
                        routine_rule += f"，重复{routine['times']}次"
                    routine_rule_label = QLabel(routine_rule)
                    delete_button = QPushButton("删除")
                    delete_button.clicked.connect(lambda checked, rid=routine['id']: self.delete_routine(rid))
                    row = self.look_main_layout.rowCount()
                    self.look_main_layout.addWidget(routine_name_label, row, 0)
                    self.look_main_layout.addWidget(routine_date_label, row, 1)
                    self.look_main_layout.addWidget(routine_rule_label, row, 2)
                    self.look_main_layout.addWidget(delete_button, row, 3)
        except:
            no_routine_label = QLabel("暂无日程")
            self.look_main_layout.addWidget(no_routine_label)

        self.window_look.setLayout(self.look_main_layout)
        self.window_look.setWindowIcon(QIcon("icon.png"))
        self.window_look.show()

    def delete_routine(self, rid): #删除日程
        try:
            with open(f"routine.json","r",encoding="utf-8") as f:
                jsonload = json.load(f)
            jsonload = [r for r in jsonload if r['id'] != rid]
            with open(f"routine.json","w",encoding="utf-8") as f:
                json.dump(jsonload,f,ensure_ascii=False,indent=2)
            self.window_look.close()
            self.look_button_clicked()
        except:
            show_error_window("删除日程时出错！")


# 日程查询按钮点击事件

class SearchWindow(QWidget):
    def __init__(self):
        super().__init__()
    #窗口展示
    def search_button_clicked(self):
        self.window_search = QWidget()
        self.window_search.setWindowTitle("日期查询")
        self.window_search.setGeometry(220, 220, 400, 300)
        self.chooseday_label = QLabel("选择日期：")
        self.chooseday_edit = QDateEdit()
        self.chooseday_edit.setCalendarPopup(True)
        self.chooseday_edit.setDate(QDate.currentDate())
        self.search_button =QPushButton("查询")
        self.search_button.clicked.connect(self.perform_search)
        self.search_widget = QWidget()
        self.search_layout = QHBoxLayout(self.search_widget)
        self.search_layout.addWidget(self.chooseday_label)
        self.search_layout.addWidget(self.chooseday_edit)
        self.search_layout.addWidget(self.search_button)
        self.search_main_layout = QVBoxLayout()
        self.window_layout = QVBoxLayout()
        self.window_layout.addWidget(self.search_widget  )
        self.window_layout.addLayout(self.search_main_layout)
        self.window_search.setLayout(self.window_layout)
        self.window_search.setWindowIcon(QIcon("icon.png"))
        self.window_search.show()
    # 查询功能实现    
    def perform_search(self):
        # 清空上一次的查询结果

        while self.search_main_layout.count():
            item = self.search_main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                child_layout = item.layout()
                while child_layout.count():
                    child_item = child_layout.takeAt(0)
                    if child_item.widget():
                        child_item.widget().deleteLater()
                child_layout.deleteLater()

        # 输出查询结果

        self.gongli_label = QLabel(f"公历日期：{self.chooseday_edit.date().year()}年{self.chooseday_edit.date().month()}月{self.chooseday_edit.date().day()}日 星期{weeknum_to_chinese(self.chooseday_edit.date().dayOfWeek())}")
        lunar = lunar_chinese(self.chooseday_edit.date())
        self.nongli_label =QLabel(f"农历日期：农历{lunar[2]}年{lunar[0]}{lunar[1]}")
        self.todayroutine_label = QLabel("日程：")
        self.search_main_layout.addWidget(self.gongli_label)
        self.search_main_layout.addWidget(self.nongli_label)
        self.search_main_layout.addWidget(self.todayroutine_label)

        # 判断日期是否被查询。
        with open(f"routine.json","r",encoding="utf-8") as f:
                jsonload = json.load(f)
                self.num = 0
                for routine in jsonload:
                    routine_date = QDate.fromString(routine['date'], "yyyy-MM-dd")
                    rouexlist = []
                    if routine['except'] != []:
                        for x in routine['except']:
                            rouexlist.append(QDate.fromString(x, "yyyy-MM-dd"))
                    date = self.chooseday_edit.date()
                    self.istodayroutine = is_today_routine(date,routine_date,rouexlist,routine['rule'],routine.get('days',1),routine['times']) # 采用is_today_routine函数判断当天是否有该日程
                    if self.istodayroutine:
                        new_lan = QHBoxLayout()
                        routine_label = QLabel(f"{routine['name']}：{routine['description']}")
                        routine_label.setWordWrap(True)
                        edit_button = QPushButton("编辑")
                        edit_button.clicked.connect(partial(self.edit_button_clicked,routine['id'],routine['name'],routine['description'],self.chooseday_edit.date().toString('yyyy-MM-dd')))
                        new_lan.addWidget(routine_label)
                        new_lan.addWidget(edit_button)
                        self.search_main_layout.addLayout(new_lan) 
                        self.num += 1
                    else:
                        continue
                if self.num == 0:
                    routine_label = QLabel("暂无日程")
                    new_lan = QHBoxLayout()
                    new_lan.addWidget(routine_label)
                    self.search_main_layout.addLayout(new_lan)

    def edit_button_clicked(self,rid,name,desc,time): #编辑窗口
        self.window_edit = QWidget()
        self.window_edit.setWindowTitle("编辑日程")
        self.window_edit.setGeometry(220, 220, 400, 300)
        self.date_label = QLabel(f"日期：{time}")
        self.name_label = QLabel(f"日程名称：{name}")
        self.name_edit = QPushButton("编辑")
        self.name_edit.clicked.connect(lambda:self.show_line_edit(self.name_edit_text))
        self.name_edit_text = QLineEdit()
        self.name_edit_text.setVisible(False)
        self.name_layout = QHBoxLayout()
        self.name_layout.addWidget(self.name_label)
        self.name_layout.addWidget(self.name_edit)
        self.name_layout.addWidget(self.name_edit_text)
        self.desc_label = QLabel(f'日程描述：{desc}')
        self.desc_edit = QPushButton("编辑")
        self.desc_edit.clicked.connect(lambda:self.show_line_edit(self.desc_edit_text))
        self.desc_edit_text = QLineEdit()
        self.desc_edit_text.setVisible(False)
        self.desc_layout = QHBoxLayout()
        self.desc_layout.addWidget(self.desc_label)
        self.desc_layout.addWidget(self.desc_edit)
        self.desc_layout.addWidget(self.desc_edit_text)
        self.deltoday_button =QPushButton("删除当日日程")
        self.deltoday_button.clicked.connect(lambda: self.delete_today(rid,time))
        self.delall_button = QPushButton("删除所有日程")
        self.delall_button.clicked.connect(lambda: self.delete_all(rid,time))
        self.delfuture_button = QPushButton("删除未来日程")
        self.delfuture_button.clicked.connect(lambda:self.delete_future(rid,time))
        self.savetoday_button = QPushButton("将修改应用到当天")
        self.savetoday_button.clicked.connect(lambda: self.save_today(rid,time,self.name_edit_text.text() if self.name_edit_text.text() != '' else name,self.desc_edit_text.text() if self.desc_edit_text.text() != '' else desc))
        self.saveall_button = QPushButton("将修改应用到全局")
        self.saveall_button.clicked.connect(lambda: self.save_all(rid,time,self.name_edit_text.text() if self.name_edit_text.text() != '' else name,self.desc_edit_text.text() if self.desc_edit_text.text() != '' else desc))
        self.edit_layout = QHBoxLayout()
        self.edit_layout.addWidget(self.deltoday_button)
        self.edit_layout.addWidget(self.delall_button)
        self.edit_layout.addWidget(self.delfuture_button)
        self.edit_layout.addWidget(self.savetoday_button)
        self.edit_layout.addWidget(self.saveall_button)
        self.edit_main_layout = QVBoxLayout()
        self.edit_main_layout.addWidget(self.date_label)
        self.edit_main_layout.addLayout(self.name_layout)
        self.edit_main_layout.addLayout(self.desc_layout)
        self.edit_main_layout.addLayout(self.edit_layout)
        self.window_edit.setLayout(self.edit_main_layout)
        self.window_edit.setWindowIcon(QIcon("icon.png"))
        self.window_edit.show()
    
    def delete_today(self,rid,time): #删除当日日程。实现逻辑是：1.如果日程不重复，直接删除该日程。2.如果日程重复，在例外列表中添加当天日期。
            n = 0
            with open(f"routine.json","r",encoding="utf-8") as f:
                jsonload = json.load(f)
                for x in jsonload:
                    if x['id'] == rid:
                        if x['rule'] != "不重复":
                            if x['except'] == []:
                                x['except'] = [time]
                            else:
                                if time not in x['except']:
                                    x['except'].append(time)
                            n = 1

            if n == 1:
                with open(f"routine.json","w",encoding="utf-8") as f:
                    json.dump(jsonload,f,ensure_ascii=False,indent=2)
                self.window_edit.close()
                self.window_search.close()
                self.search_button_clicked()
                self.chooseday_edit.setDate(QDate.fromString(time,'yyyy-MM-dd'))
                self.perform_search()
            else:
                self.delete_all(rid,time)


    def delete_all(self,rid,time): # 删除所有日程
        try:
            with open(f"routine.json","r",encoding="utf-8") as f:
                jsonload = json.load(f)
            jsonload = [r for r in jsonload if r['id'] != rid]
            with open(f"routine.json","w",encoding="utf-8") as f:
                json.dump(jsonload,f,ensure_ascii=False,indent=2)
        except:
            show_error_window("删除日程时出错！")
        self.window_edit.close()
        self.window_search.close()
        self.search_button_clicked()
        self.chooseday_edit.setDate(QDate.fromString(time,'yyyy-MM-dd'))
        self.perform_search()

    def show_line_edit(self,lineedit:QLineEdit):
        if lineedit.isVisible():
            lineedit.setVisible(False)
            lineedit.clear()
        else:
            lineedit.setVisible(True)

    # 将更改保存到当天，实现逻辑是：1.在日程文件中新建一个不重复的日程，名称和描述为修改后的内容，时间为当天日期。2.在原日程中添加当天日期到例外列表。
    def save_today(self,rid,time,name,desc):
        with open(f"routine.json","r",encoding="utf-8") as f:
            jsonload = json.load(f)
            max_id = max(r["id"] for r in jsonload)
            new_id = max_id + 1
            for x in jsonload:
                if x['id'] == rid:
                    target = x
                    break
            if not (target['name'] == name and target['description'] == desc):
                jsonload.append({
                "id": new_id,
                "name": name,
                "date": time,
                "rule": '不重复',
                "times": 0,
                "except": [],
                "description": desc
                })
                with open(f"routine.json","w",encoding="utf-8") as f:
                    json.dump(jsonload,f,ensure_ascii=False,indent=2)
                self.delete_today(rid,time)
    
    # 将更改保存到全局，实现逻辑是：1.在日程文件中新建一个与原日程重复规则相同的日程，名称和描述为修改后的内容。2.删除原日程。
    def save_all(self,rid,time,name,desc):
        with open(f"routine.json","r",encoding="utf-8") as f:
            jsonload = json.load(f)
            max_id = max(r["id"] for r in jsonload)
            new_id = max_id + 1
            for x in jsonload:
                if x['id'] == rid:
                    target = x
                    break
            if not (target['name'] == name and target['description'] == desc):
                if target['rule'] == '每...天':
                    jsonload.append({
                        "id": new_id,
                        "name": name,
                        "date": target['date'],
                        "rule": target['rule'],
                        "times": target['times'],
                        "days": target['days'],
                        "except": target['except'],
                        "description": desc
                    })
                else:
                    jsonload.append({
                        "id": new_id,
                        "name": name,
                        "date": target['date'],
                        "rule": target['rule'],
                        "times": target['times'],
                        "except": target['except'],
                        "description": desc
                        })
                with open(f"routine.json","w",encoding="utf-8") as f:
                    json.dump(jsonload,f,ensure_ascii=False,indent=2)
                self.delete_all(rid,time)

    # 删除未来日程，实现逻辑是：1.计算从日程开始日期到所选日期之间有多少次日程发生。2.新建一个从日程开始日期开始，重复次数为计算结果的新日程。3.删除原日程中从所选日期开始的所有日程。
    def delete_future(self,rid,time):
        with open(f"routine.json","r",encoding="utf-8") as f:
            jsonload = json.load(f)
            max_id = max(r["id"] for r in jsonload)
            new_id = max_id + 1
            for x in jsonload:
                if x['id'] == rid:
                    target = x
                    break
            dateq = QDate.fromString(time,'yyyy-MM-dd')
            rdateq = QDate.fromString(target['date'],'yyyy-MM-dd')
            startdate = rdateq
            newtimes = 0
            for i in range(rdateq.daysTo(dateq)+1):
                if is_today_routine(startdate,rdateq,target['except'],target['rule'],target.get('days',1),target['times']):
                    newtimes += 1
                startdate = startdate.addDays(1)
            if target['rule'] == '每...天':
                jsonload.append({
                    "id": new_id,
                    "name": target['name'],
                    "date": target['date'],
                    "rule": target['rule'],
                    "times": newtimes + len(target['except']),
                    "days": target['days'],
                    "except": target['except'],
                    "description": target['description']
                    })
            else:
                jsonload.append({
                    "id": new_id,
                    "name": target['name'],
                    "date": target['date'],
                    "rule": target['rule'],
                    "times": newtimes + len(target['except']),
                    "except": target['except'],
                    "description": target['description']
                    })
            with open(f"routine.json","w",encoding="utf-8") as f:
                    json.dump(jsonload,f,ensure_ascii=False,indent=2)
            self.delete_all(rid,time)

        
            
# 画日历。

class MCalendarWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 设置日历控件

        self.calendar = lunarCalendar()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
        self.calendar.setFirstDayOfWeek(Qt.Monday)
        self.calendar.setDateEditEnabled(False)
        self.calendar.setNavigationBarVisible(False)
        self.calendar.setFont(QFont("Arial", 12))

        # 设置顶栏
        self.header_widget = QWidget(self) # 创建顶栏部件
        self.header_layout = QHBoxLayout(self.header_widget) # 创建水平布局
        self.leftbutton = QPushButton("<", self.header_widget) # 创建左按钮
        self.rightbutton = QPushButton(">", self.header_widget) # 创建右按钮
        self.label = QLabel(self) # 创建标签
        self.label.setFont(QFont("Arial", 20)) # 设置标签字体
        self.label.setAlignment(Qt.AlignCenter) # 设置标签居中
        self.header_layout.addWidget(self.leftbutton) # 添加左按钮到布局
        self.header_layout.addWidget(self.label,stretch=1) # 添加标签到布局
        self.header_layout.addWidget(self.rightbutton) # 添加右按钮到布局
        self.header_layout.setContentsMargins(0, 0, 0, 0) # 设置布局边距
        self.leftbutton.clicked.connect(self.show_previous_month) # 连接左按钮点击事件
        self.rightbutton.clicked.connect(self.show_next_month) # 连接右按钮点击事件
        self.calendar.currentPageChanged.connect(self.update_header) # 连接页面改变事件
        self.update_header() # 初始化标签文本

        # 设置主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.header_widget)
        self.main_layout.addWidget(self.calendar)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

    def show_previous_month(self):
        self.calendar.showPreviousMonth()
        self.update_header()

    def show_next_month(self):
        self.calendar.showNextMonth()
        self.update_header()

    def update_header(self):
        month = self.calendar.monthShown()
        year = self.calendar.yearShown()
        self.label.setText(f"{year} - {month:02d}")
    

# 农历与日程绘制

class lunarCalendar(QCalendarWidget):
    def __init__(self):
        super().__init__()
    def paintCell(self, painter, rect, date):
        painter.save()
        painter.setBrush(QColor(231, 246, 251, 160))  # 非选中背景色
        painter.setPen(Qt.NoPen)
        painter.drawRect(rect)
        painter.restore()
        if date == self.selectedDate():
            painter.save()
            radius = min(rect.width(), rect.height()) // 3 - 2
            center = rect.center()
            painter.setBrush(QColor('#66CCFF'))  # 蓝色
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)
            painter.restore()

        painter.setPen(Qt.black)

        if date.dayOfWeek() == 6 or date.dayOfWeek() == 7:  # 周末颜色
            painter.setPen(Qt.red)
        if date.month() != self.monthShown():  # 非本月日期颜色
            painter.setPen(Qt.gray)
        painter.setFont(QFont("微软雅黑", 15))
        painter.drawText(rect, Qt.AlignCenter, str(date.day()))

        # 绘制农历
        painter.setFont(QFont("微软雅黑", 10))
        lunar = lunar_chinese(date)
        if lunar[1] == '初一':
            painter.drawText(rect, Qt.AlignBottom | Qt.AlignRight, lunar[0])
        else:
            painter.drawText(rect, Qt.AlignBottom | Qt.AlignRight, lunar[1])

        # 读取日程文件并绘制日程
        font = QFont("微软雅黑", 8)
        font.setItalic(True)
        painter.setFont(font)
        try:
            with open(f"routine.json","r",encoding="utf-8") as f:
                jsonload = json.load(f)
                text = ""
                for routine in jsonload:
                    routine_date = QDate.fromString(routine['date'], "yyyy-MM-dd")
                    rouexlist = []
                    if routine['except'] != []:
                        for x in routine['except']:
                            rouexlist.append(QDate.fromString(x, "yyyy-MM-dd"))
                    else:
                        rouexlist.append(QDate.fromString('0001-01-01','yyyy-MM-dd'))
                    istodayroutine = is_today_routine(date,routine_date,rouexlist,routine['rule'],routine.get('days',1),routine['times']) # 采用is_today_routine函数判断当天是否有该日程
                    if istodayroutine:
                        text += routine['name'] + "\n"
                text = text.strip()
                painter.drawText(rect, Qt.AlignTop | Qt.AlignLeft, text)
        except:
            pass

#欢迎弹窗
class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("欢迎来到 MCalendar！")
        self.setFixedSize(600, 300)
        self.setWindowIcon(QIcon("icon.png"))

        #左边：Meko
        self.girl_label = QLabel()
        pixmap = QPixmap("Meko.png")
        self.girl_label.setPixmap(pixmap)
        self.girl_label.setScaledContents(True)
        self.girl_label.setFixedSize(280, 280)

        #右边：文字
        self.title_label = QLabel("欢迎来到 MCalendar！")
        self.title_label.setFont(QFont("Arial", 18))
        self.title_label.setAlignment(Qt.AlignLeft)

        self.text_label = QLabel()
        self.text_label.setFont(QFont("微软雅黑", 11))
        self.text_label.setWordWrap(True)

        self.start_button = QPushButton("开始使用")
        self.start_button.clicked.connect(self.accept)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.title_label)
        right_layout.addSpacing(10)
        right_layout.addWidget(self.text_label)
        right_layout.addStretch()
        right_layout.addWidget(self.start_button, alignment=Qt.AlignRight)

        #总布局
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.girl_label)
        main_layout.addLayout(right_layout)

        #设置文本
        self.update_today_text()

    def update_today_text(self):
        today = QDate.currentDate()
        routines_today = []
        nonetext = ["你今天没有日程哦 ✨\n好好享受这一天吧～","今天是自由的一天 ✨","今天没有安排，放松一下吧～","今天没有日程，Meko祝你有愉快的一天！",]
        havetextend = ["今天有好多日程呢！\n加油完成它们吧！","加油哦！","今天的任务可不少呢！\n一起加油吧！","今天有很多事情要做呢！\nMeko相信你能做到！",]
        try:
            with open("routine.json", "r", encoding="utf-8") as f:
                jsonload = json.load(f)
            for routine in jsonload:
                routine_date = QDate.fromString(routine['date'], "yyyy-MM-dd")
                excepts = [QDate.fromString(x, "yyyy-MM-dd") for x in routine.get('except', [])]
                if is_today_routine(today,routine_date,excepts,routine['rule'],routine.get('days', 1),routine['times']):
                    routines_today.append(routine['name'])
        except:
            pass
        if not routines_today:
            self.text_label.setText(random.choice(nonetext))
        else:
            text = "你今天的日程有：\n" + "\n".join(f"• {r}" for r in routines_today) + "\n" + random.choice(havetextend)
            self.text_label.setText(text)

# 创建主窗口

app = QApplication([])

welcome = WelcomeDialog()
welcome.setGeometry(300,350, 600, 300)
window = QWidget()

# 配置主窗口
calendar = MCalendarWidget() # 创建自定义日历控件
main_layout = QVBoxLayout()
top_layout = QHBoxLayout()
new_button = QPushButton("新建日程")
top_layout.addWidget(new_button)
new_routine_window = NewRoutineWindow()
new_button.clicked.connect(new_routine_window.new_button_clicked)
look_button = QPushButton("查看日程")
look_window = LookWindow()
look_button.clicked.connect(look_window.look_button_clicked)
top_layout.addWidget(look_button)
search_button = QPushButton("日期查询")
search_window = SearchWindow()
search_button.clicked.connect(search_window.search_button_clicked)
top_layout.addWidget(search_button)
title_label = QLabel("MCalendar  .ω.")
title_label.setFont(QFont("Arial", 24))
title_label.setStyleSheet('''
                          QLabel{
                                color: #7c34a0;
                                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #cef3fd, stop:1 #a1e7fb);
                        }''')
top_layout.addWidget(title_label)
top_layout.setSpacing(0)
top_layout.setContentsMargins(0, 0, 0, 0)
main_layout.addLayout(top_layout)
center_layout = QGridLayout()
center_layout.addWidget(calendar, 0, 0)
center_layout.setContentsMargins(0, 0, 0, 0)
main_layout.addLayout(center_layout)
window.setWindowTitle("MCalendar")
window.setWindowIcon(QIcon("icon.png"))
window.setGeometry(100, 100, 1200, 800)
window.setLayout(main_layout)

# 看板娘
bg = QLabel(window)
bg.setPixmap(QPixmap("Meko.png"))
bg.setScaledContents(True)
bg.resize(500, 500)
bgopacity = QGraphicsOpacityEffect()
bgopacity.setOpacity(0.1)
bg.setGraphicsEffect(bgopacity)
bg.setAttribute(Qt.WA_TransparentForMouseEvents)

window.show()
welcome.exec_()
app.exec_()