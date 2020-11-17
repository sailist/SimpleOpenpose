from caller import Caller
from bodyfeature import *
import sys
import typing
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap, QImage
from PyQt5 import QtCore
from PyQt5.QtWidgets import *


def open_dir(path,select=False):
    if select:
        os.system('explorer.exe /select, "%s"' % path)
    else:
        os.system("explorer.exe %s" % path)

class FirstWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("人体姿态估计")
        w = QWidget()
        self.caller = None
        self.setCentralWidget(w)
        layout = QVBoxLayout()
        w.setLayout(layout)

        layout.addLayout(self.image_area())
        layout.addLayout(self.button_area())

    def image_area(self):
        layout = QHBoxLayout()
        self.ori_lb = QLabel("Origin")
        layout.addWidget(self.ori_lb)
        self.pose_lb = QLabel("PoseLabeled")
        layout.addWidget(self.pose_lb)

        return layout

    def show_feature_imgage(self, fname, label: QLabel):
        image = QImage(fname)
        label.setPixmap(QPixmap.fromImage(image))

    def button_area(self):
        layout = QHBoxLayout()
        left = QVBoxLayout()
        layout.addLayout(left)

        self.state_lb = QLabel("身体状态：  ；手部状态：  ")
        left.addWidget(self.state_lb)

        reco_bt = QPushButton("识别")
        reco_bt.clicked.connect(self.reco_pose)
        layout.addWidget(reco_bt)
        open_dir_bt = QPushButton("打开识别文件夹")
        open_dir_bt.setDisabled(True)
        self.open_dir_bt = open_dir_bt
        open_dir_bt.clicked.connect(self.open_reco_dir)
        layout.addWidget(open_dir_bt)

        return layout

    def open_reco_dir(self):
        open_dir(self.caller.render_dir)

    def reco_pose(self):
        self.setCursor(Qt.BusyCursor)
        fname = QFileDialog.getOpenFileName(self, 'Open file', os.getcwd())
        print(fname)
        if not fname[0]:
            self.setCursor(Qt.ArrowCursor)
            return

        self.caller = Caller(fname[0])
        self.caller.start()
        self.caller.wait()
        self.pose = Pose(self.caller.json_fs[0])
        is_raise = self.pose.body.is_raise()
        is_lie = self.pose.body.is_lie()
        is_sit = self.pose.body.is_sit()
        is_stand = self.pose.body.is_stand()

        if is_lie:
            st = "躺"
        elif is_sit:
            st = "坐"
        elif is_stand:
            st = "站"
        else:
            st = "无法判断"
        if is_raise:
            st = "身体状态：{}; 手部状态：举手".format(st)
        else:
            st = "身体状态：{}; 手部状态：无".format(st)

        self.state_lb.setText(st)
        self.show_feature_imgage(self.caller.fs[0],self.ori_lb)
        self.show_feature_imgage(self.caller.render_fs[0],self.pose_lb)
        self.open_dir_bt.setDisabled(False)
        self.setCursor(Qt.ArrowCursor)
        self.setFixedSize(0,0)


if __name__ == "__main__":
    App = QApplication(sys.argv)
    ex = FirstWindow()
    ex.show()

    sys.exit(App.exec_())