import ctypes
import linecache
import sys, math, requests
import re

import cchardet as cchardet
from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtGui import QPixmap, QPainter, QImage, QPalette, QBrush, QFont, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLabel, QFileDialog, QFontDialog, QColorDialog, \
    QTreeWidgetItem
from QtDesigner.UI.UI_Reader import Ui_MainWindow  # 导入 uiDemo10.py 中的 Ui_MainWindow 界面类

# 加上这段话，在运行程序时，设置的窗口图标才会出现
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")

class MyMainWindow(QMainWindow, Ui_MainWindow):  # 继承 QMainWindow 类和 Ui_MainWindow 界面类
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)  # 初始化父类
        self.setupUi(self)  # 继承 Ui_MainWindow 界面类
        # 加载设置
        self.init_info()
        # 开局先隐藏按钮
        self.last.setHidden(True)
        self.next.setHidden(True)
        # 显示上次打开的文件
        if self.cur_file:
            self.load_file(self.cur_file)
        # 设置窗口大小
        self.resize(int(self.win[0]), int(self.win[1]))
        # 设置默认背景色
        self.treeWidget.setStyleSheet(f"background-color: rgba({self.color[0]}, {self.color[1]}, {self.color[2]},0.5);border: 1px solid #000000;border-color: rgb({self.color[0]}, {self.color[1]}, {self.color[2]})")
        self.textBrowser.setStyleSheet(f"background-color: rgba({self.color[0]}, {self.color[1]}, {self.color[2]},0.5);border: 1px solid #000000;border-color: rgb({self.color[0]}, {self.color[1]}, {self.color[2]})")
        # 设置目录栏初始为隐藏状态
        self.treeWidget.setHidden(True)
        # 点击目录显示/隐藏目录
        self.catlog.triggered.connect(self.tab_catlog)
        # 打开文件
        self.fileopen.triggered.connect(self.open_file)
        # self.setStyleSheet("#MainWindow{background-image: url(:/img/default.png);}")
        # 设置字体和颜色
        self.actionfont.triggered.connect(self.select_font)
        self.actioncolor.triggered.connect(self.select_color)
        # 设置背景图片
        self.actionimport.triggered.connect(self.select_bg)
        # 关闭背景图片
        self.actionclose.triggered.connect(self.close_bg)
        # 恢复默认设置
        self.actiondefaults.triggered.connect(self.default)
        self.setAutoFillBackground(True)
        # self.__pic = QPixmap("./static/img/default.png")
        # 上一章，下一章按钮点击事件
        self.last.clicked.connect(self.show_last)
        self.next.clicked.connect(self.show_next)

    def paintEvent(self, event):
        painter = QPainter(self)
        # img = self.__pic.scaled(self.width(), self.height(),
        #                     Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(self.rect(), QPixmap(self.bg))
        super().paintEvent(event)

    # 显示/隐藏目录
    def tab_catlog(self):
        if self.treeWidget.isVisible():
            self.treeWidget.setHidden(True)
        else:
            self.treeWidget.setVisible(True)

    # 打开文件
    def open_file(self):
        # 弹出QFileDialog窗口。getOpenFileName()方法的第一个参数是说明文字，
        # 第二个参数是默认打开的文件夹路径。默认情况下显示所有类型的文件。
        if not self.cur_file:
            path = '/'
        else:
            path = self.cur_file
        fname = QFileDialog.getOpenFileName(self, '打开文件', path, filter='*.txt')
        self.load_file(fname[0])

    # 显示最近的文件
    def show_last_file(self):
        # 每次绘制时将之前的清空
        self.openlastfile.clear()
        _translate = QtCore.QCoreApplication.translate
        for i, file in enumerate(self.last_files):
            # 截取文件名
            name = file.split('/')[-1].split('.')[0]
            # 添加action
            action = QtWidgets.QAction(self)
            action.setObjectName(f'file{i}')    # 设置对象名
            self.openlastfile.addAction(action)  # 添加到菜单栏中
            action.setText(_translate("MyMainWindow", name))    # 添加到主窗口，且设置text
            action.triggered.connect(self.open_last_file)   # 设置触发事件

    # 设置章节目录
    def setChapters(self):
        # 每次绘制目录时先清除一下
        self.treeWidget.clear()
        _translate = QtCore.QCoreApplication.translate
        __sortingEnabled = self.treeWidget.isSortingEnabled()
        for i, value in enumerate(self.chapters):
            item = QTreeWidgetItem(self.treeWidget)
            item.setText(0, _translate("MyMainWindow", list(value.keys())[0]))
            self.treeWidget.addTopLevelItem(item)
            # print(self.treeWidget.topLevelItem(i))
            # self.treeWidget.topLevelItem(i).setText(0, _translate("MyMainWindow", value.keys()[0]))
        self.treeWidget.setSortingEnabled(__sortingEnabled)
        self.treeWidget.clicked.connect(self.onTreeClicked)
        self.treeWidget.setCurrentItem(self.treeWidget.topLevelItem(self.chapter),0)
        # 为当前章节设置背景色
        self.treeWidget.topLevelItem(self.chapter).setBackground(0, QColor(15,136,235))

    def load_file(self, file):
        # 文件不为空
        if file:
            try:
            # 打开新文件时重置章节
                if not self.last_files or self.cur_file != self.last_files[-1]:
                    self.chapter = 0
                # 更改目前打开的文件
                self.cur_file = file
                self.filename = file.split('/')[-1].split('.')[0]
                # 将打开的文件添加到最近文件中去
                # 如果文件存在，则要更改文件的打开顺序
                if file in self.last_files:
                    self.last_files.remove(file)
                self.last_files.append(file)
                # 只存储最近打开的五本书籍
                if len(self.last_files) > 5:
                    self.last_files.pop(0)
                # 获取文件的编码格式
                encodings = self.get_encoding(file)
                with open(file, 'r', encoding=encodings) as f:
                    # 打开文件,生成章节目录
                    self.chapters = []
                    # 包含了txt文本的全部内容
                    self.lines = f.readlines()
                    # 一种匹配章节目录的规则
                    pattern = r"(第)([\u4e00-\u9fa5a-zA-Z0-9]{1,7})[章|节][^\n]{1,35}(|\n)"
                    for i in range(len(self.lines)):
                        line = self.lines[i].strip()
                        if line != "" and re.match(pattern, line):
                            line = line.replace("\n", "").replace("=", "")
                            if len(line) < 30:
                                self.chapters.append({line: i})
                # 如果没有可用的目录,那就显示全部
                if not self.chapters:
                    self.chapters.append({self.filename: 0})
                # print(self.chapters)
                 # 显示最近打开的文件
                self.show_last_file()
                # 设置章节目录
                self.setChapters()
                # 设置文本浏览器的内容
                self.show_content()
            except:
                self.show_msg('文件不存在或者错误！')
        else:   # 文件为空，说明没有选择文件
            self.show_msg('您没有选择文件！')
    # 打开最近的文件
    def open_last_file(self):
        sender = self.sender().objectName()  # 获取当前信号 sender
        # 根据我们设置的对象名，截取字符，然后从配置文件寻找文件路径
        self.load_file(self.last_files[int(sender[-1])])

    # 选择字体
    def select_font(self):
        # 弹出一个字体选择对话框。getFont()方法返回一个字体名称和状态信息。
        # 状态信息有OK和其他两种。
        font, ok = QFontDialog.getFont(QFont(self.fonts, self.fontsize), self, '选择字体和大小')
        # 如果点击OK，标签的字体就会随之更改
        if ok:
            self.textBrowser.setFont(font)
            self.fonts = font.family()
            self.fontsize = font.pointSize()

    # 选择颜色
    def select_color(self):
        col = QColorDialog.getColor(self.textBrowser.textColor(), self, "设置背景颜色")
        if col.isValid():
            print(col)
            self.treeWidget.setStyleSheet(
                f"background-color: rgba({col.red()}, {col.green()}, {col.blue()},0.5);border: 1px solid #000000;border-color: rgb({col.red()}, {col.green()}, {col.blue()})")
            self.textBrowser.setStyleSheet(
                f"background-color: rgba({col.red()}, {col.green()}, {col.blue()},0.5);border: 1px solid #000000;border-color: rgb({col.red()}, {col.green()}, {col.blue()})")
            self.color = [col.red(), col.green(), col.blue()]


    # 选择背景图片
    def select_bg(self):
        if not self.bg:
            path = '/'
        else:
            path = self.bg
        fname = QFileDialog.getOpenFileName(self, '选择图片', path, filter='*.jpg,*.png,*.jpeg,All Files(*)')
        # 文件不为空
        if fname[0]:
            try:
                # 更改目前的背景图片
                self.bg = fname[0]
                self.update()   # 刷新页面
            except:
                self.show_msg('文件不存在或者错误！')
        else:  # 文件为空，说明没有选择文件
            self.show_msg('您没有选择文件！')

    # 关闭背景图片
    def close_bg(self):
        self.bg = ''    # 将背景图片设置为空即可
        self.update()   # 刷新页面

    # 恢复默认设置
    def default(self):
        result = QMessageBox.question(self, "恢复默认设置", "确定恢复默认设置？这将使您的设置全部失效且关闭应用",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if result == QMessageBox.Yes:
            # 重新配置设置文件
            self.setting.setValue("SCREEN/screen", self.setting.value("DEFAULT/screen"))
            self.setting.setValue("FILE/file", self.setting.value("DEFAULT/file"))
            self.setting.setValue("FILE/files", self.setting.value("DEFAULT/files"))
            self.setting.setValue("BACKGROUND/bg", self.setting.value("DEFAULT/bg"))
            self.setting.setValue("BACKGROUND/color", self.setting.value("DEFAULT/color"))
            self.setting.setValue("FONT/font", self.setting.value("DEFAULT/font"))
            self.setting.setValue("FONT/fontsize", self.setting.value("DEFAULT/fontsize"))
            QtCore.QCoreApplication.instance().quit()

    # 点击目录跳转到章节
    def onTreeClicked(self, index):
        # 恢复原来章节的背景色(设置透明度为0)，为新章节设置背景色
        self.treeWidget.topLevelItem(self.chapter).setBackground(0, QColor(0,0,0, 0))
        # 获取点击的项目下标
        self.chapter = int(index.row())
        # 判断按钮是否要显示
        self.show_button()
        self.treeWidget.topLevelItem(self.chapter).setBackground(0, QColor(15,136,235))
        self.show_content()


    # 获取章节内容
    def get_content(self):
        index = self.chapter
        # 起始行
        start = list(self.chapters[index].values())[0]
        # 如果是终章
        if index == self.treeWidget.topLevelItemCount() - 1:
            return "".join(self.lines[start:-1])
        else:
            # 终止行
            end = list(self.chapters[index + 1].values())[0]
            return "".join(self.lines[start:end])

    # 设置文本浏览器的内容
    def show_content(self):
        # 在展示内容时直接判断按钮是否要隐藏
        self.show_button()
        # 将文件内容添加到文本浏览器中
        self.textBrowser.setText(self.get_content())
        # 设置字体和大小
        self.textBrowser.setFont(QFont(self.fonts, self.fontsize))
        # 状态栏显示当前的章节内容和目录名
        self.textBrowser.setStatusTip(self.filename + "   " +list(self.chapters[self.chapter].keys())[0])

    # 展示上一章
    def show_last(self):
        # 更改目录背景色
        self.treeWidget.topLevelItem(self.chapter).setBackground(0, QColor(0, 0, 0, 0))
        self.chapter = self.chapter - 1
        self.show_content() # 显示内容
        self.treeWidget.topLevelItem(self.chapter).setBackground(0, QColor(15, 136, 235))

    # 展示下一章
    def show_next(self):
        # 更改目录背景色
        self.treeWidget.topLevelItem(self.chapter).setBackground(0, QColor(0, 0, 0, 0))
        self.chapter = self.chapter + 1
        self.show_content() # 显示内容
        self.treeWidget.topLevelItem(self.chapter).setBackground(0, QColor(15, 136, 235))

    # 根据显示的章节来决定按钮是否要改动，简单一点，直接隐藏按钮
    def show_button(self):
        # 考虑只有一个章节的情况
        if len(self.chapters) == 1:
            self.last.setHidden(True)
            self.next.setHidden(True)
        # 第一章
        elif self.chapter == 0:
            self.last.setHidden(True)
            self.next.setVisible(True)
        # 末章
        elif self.chapter == len(self.chapters) - 1:
            self.last.setVisible(True)
            self.next.setHidden(True)
        # 其他情况，恢复按钮
        else:
            if self.last.isHidden():
                self.last.setVisible(True)
            if self.next.isHidden():
                self.next.setVisible(True)

    # 初始化设置
    def init_info(self):
        self.setting = QtCore.QSettings("./config.ini", QtCore.QSettings.IniFormat)   # 配置文件
        self.setting.setIniCodec('utf-8')   # 设置配置文件的编码格式
        self.win = self.setting.value("SCREEN/screen")  # 窗口大小
        self.cur_file = self.setting.value("FILE/file")     # 目前打开的文件
        self.chapter = int(self.setting.value("FILE/chapter"))   # 上次浏览的章节
        self.last_files = self.setting.value("FILE/files")  # 最近打开的文件
        if not self.last_files:
            self.last_files = []
        self.bg = self.setting.value("BACKGROUND/bg")   # 背景图片
        self.color = self.setting.value("BACKGROUND/color") # 背景颜色
        self.fonts = self.setting.value("FONT/font")    # 字体
        self.fontsize = int(self.setting.value("FONT/fontsize")) # 字体大小

    # 保存设置
    def save_info(self):
        self.setting.setValue("SCREEN/screen", self.win)
        self.setting.setValue("FILE/file", self.cur_file)
        self.setting.setValue("FILE/chapter", self.chapter)
        self.setting.setValue("FILE/files", self.last_files)
        self.setting.setValue("BACKGROUND/bg", self.bg)
        self.setting.setValue("BACKGROUND/color", self.color)
        self.setting.setValue("FONT/font", self.fonts)
        self.setting.setValue("FONT/fontsize", self.fontsize)

    def show_msg(self, msg):
        # 后两项分别为按钮(以|隔开，共有7种按钮类型，见示例后)、默认按钮(省略则默认为第一个按钮)
        reply = QMessageBox.information(self, "提示", msg, QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)
    # 获取文件编码类型
    def get_encoding(self, file):
        # 二进制方式读取，获取字节数据，检测类型
        with open(file, 'rb') as f:
            return cchardet.detect(f.read())['encoding']

    # 窗口移动事件，保存用户最后设置的窗口大小
    def resizeEvent(self, event):
        self.win = [event.size().width(), event.size().height()]

    # 关闭窗口时更新窗口大小
    def closeEvent(self, event):
        result = QMessageBox.question(self, "关闭应用", "确定关闭应用？",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if result == QMessageBox.Yes:
            # 在关闭窗口时保存设置
            self.save_info()
            event.accept()
            QMainWindow.closeEvent(self, event)
        else:
            event.ignore()




if __name__ == '__main__':
    app = QApplication(sys.argv)  # 在 QApplication 方法中使用，创建应用程序对象
    myWin = MyMainWindow()  # 实例化 MyMainWindow 类，创建主窗口
    myWin.show()  # 在桌面显示控件 myWin
    sys.exit(app.exec_())  # 结束进程，退出程序
