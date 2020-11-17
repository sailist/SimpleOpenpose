import json
from collections import namedtuple

import numpy as np

trunk = namedtuple('trunk', ['vector', 'confi', 'confj', 'useable'])


def degree(x, y=np.array([1, 0])):
    """
    输入两个向量，返回两向量夹角
    输入一个向量，返回该向量方位角
    :param x:
    :param y:
    :return:
    """
    # x=np.array([1,0])
    # y=np.array([-1,-1])
    # 两个向量
    Lx = np.sqrt(x.dot(x))
    Ly = np.sqrt(y.dot(y))
    # 相当于勾股定理，求得斜线的长度
    cos_angle = x.dot(y) / (Lx * Ly)
    # 求得cos_sita的值再反过来计算，绝对长度乘以cos角度为矢量长度，初中知识。。
    # print(cos_angle)
    angle = np.arccos(cos_angle)
    angle2 = angle * 360 / 2 / np.pi
    return angle2


def length(x):
    """返回向量长度"""
    return np.sqrt(x.dot(x))


class Pose():
    def __init__(self, jsonfn):
        with open(jsonfn, encoding='utf-8') as f:
            self.info = json.load(f)
        kpoints = self.info['people'][0]['pose_keypoints_2d']
        xs, ys, cs = [], [], []
        points = []

        for i in range(0, len(kpoints), 3):
            x, y, c = kpoints[i], kpoints[i + 1], kpoints[i + 2]
            #     if c != 0:
            xs.append(x)
            ys.append(y)
            cs.append(c)
            points.append([x, y])
        points = np.array(points)
        self.body = Body(points, cs)
        self.points = points
        self.xs, self.ys, self.confidence = xs, ys, cs


class Body:
    def __init__(self, points, confi):
        self.points = np.array(points)
        self.c = confi
        self.standard = length(self.points[1]-self.points[8])


    def create_trunk(self, i, center):
        return trunk(self.points[i] - self.points[center], self.c[i], self.c[center],
                     self.c[i] > 0.0 and self.c[center] > 0.0 and length(self.points[i] - self.points[center]) > self.standard * 0.1)

    @property
    def lleg_in(self):
        return self.create_trunk(12, 13)

    @property
    def lleg_out(self):
        return self.create_trunk(14, 13)

    @property
    def rleg_in(self):
        return self.create_trunk(9, 10)

    @property
    def body(self):
        return self.create_trunk(1, 8)

    @property
    def rleg_out(self):
        return self.create_trunk(11, 10)

    @property
    def larm_in(self):
        return self.create_trunk(5, 6)

    @property
    def larm_out(self):
        return self.create_trunk(7, 6)

    @property
    def rarm_in(self):
        return self.create_trunk(2, 3)

    @property
    def rarm_out(self):
        return self.create_trunk(4, 3)

    @property
    def head(self):
        return self.create_trunk(0, 1)

    @property
    def lshoulder(self):
        return self.create_trunk(5, 1)

    @property
    def rshoulder(self):
        return self.create_trunk(2, 1)

    def is_stand(self):
        """
        判断是否站立

        当前判断逻辑：分别判断左右腿，有一条满足则为站立
            每条腿判断逻辑：
                两条腿长度比例相差不超过20%，
                大腿和小腿夹角超过150°，
                每条腿和水平线的距离大于75°（近乎垂直）

        :return:
        """
        if self.is_lie():
            return False

        if self.lleg_in.useable and self.lleg_out.useable:
            x, y = self.lleg_in.vector, self.lleg_out.vector
            if abs(length(x) - length(y)) / length(x) < 0.2 and degree(x, y) > 150 and degree(x) > 75 and degree(
                    y) > 75:
                return True

        if self.rleg_in.useable and self.rleg_out.useable:
            x, y = self.rleg_in.vector, self.rleg_out.vector
            if abs(length(x) - length(y)) / length(x) < 0.2 and degree(x, y) > 150 and degree(x) > 75 and degree(
                    y) > 75:
                return True

        return False

    def _is_raise(self, x, y):
        if degree(y, np.array([0, -1])) < 45 and y[1] < 0:
            return True
        # if degree(x, y) < 45 and degree(y) > 60:
        #     return True
        return False

    def is_raise(self):
        """
        判断是否举手

        当前判断逻辑：
            分左右手分别判断，有一只手为举起，则返回举手状态
            每只手判断逻辑：判断小臂对应向量（6->7和3->4）与竖直方向夹角是否小于45°，且y轴方向是否向上
                （由于手势没有办法判断的很细，所以第一张看手机也被认为是举手）

        :return:
        """
        if self.larm_in.useable and self.larm_out.useable:
            if self._is_raise(self.larm_in.vector, self.larm_out.vector):
                return True

        if self.rarm_in.useable and self.rarm_out.useable:
            if self._is_raise(self.rarm_in.vector, self.rarm_out.vector):
                return True
        return False

    def is_sit(self):
        """
        判断是否坐下

        当前判断逻辑：
            首先判断是否躺下，如果躺下则返回False
            如果没有躺下，则依次判断左右腿的状态。
                根据三角形两边之和大于第三边的原理，判断两腿的向量长度，以及脚踝到胯部的向量长度（11->9和14->12）
                    （两条大腿向量为13->12和10->9，小腿向量为13->14和10->11)
                    如果大腿和小腿长大于第三边向量长度的某个倍数，则为坐下
                        （由于站直时候也是三角形，因此需要超过一定阈值，来确保弯曲程度）
                        （用大腿和小腿夹角判断也可以，只是判断的时候用了三角形三边）
                两条腿有一条满足则为坐下的状态
        :return:
        """
        if self.is_lie():
            return False

        if self.lleg_in.useable and self.lleg_out.useable:
            x, y = self.lleg_in.vector, self.lleg_out.vector
            third = self.create_trunk(9, 11)
            if third.useable:
                if length(x) + length(y) > length(third.vector) * 1.20:
                    return True

        if self.rleg_in.useable and self.rleg_out.useable:
            x, y = self.rleg_in.vector, self.rleg_out.vector
            third = self.create_trunk(9, 11)
            if third.useable:
                if length(x) + length(y) > length(third.vector) * 1.20:
                    return True

        return False

    def is_lie(self):
        """
        判断是否躺下

        当前判断标准：判断身体躯干向量（8->1)与水平方向的夹角（小于90°的），如果夹角小于45°则为躺下
        :return:
        """
        if self.body.useable:
            x = self.body.vector
            dg = degree(x)
            if dg > 90:
                dg = 180 - dg
            if dg < 45:
                return True

        return False


if __name__ == '__main__':
    jsonfs = ['.\\output\\1_keypoints.json', '.\\output\\10_keypoints.json', '.\\output\\11_keypoints.json',
              '.\\output\\12_keypoints.json', '.\\output\\13_keypoints.json', '.\\output\\2_keypoints.json',
              '.\\output\\3_keypoints.json', '.\\output\\4_keypoints.json', '.\\output\\5_keypoints.json',
              '.\\output\\6_keypoints.json', '.\\output\\7_keypoints.json', '.\\output\\8_keypoints.json',
              '.\\output\\9_keypoints.json']
    renderfs = ['.\\output\\1_rendered.png', '.\\output\\10_rendered.png', '.\\output\\11_rendered.png',
                '.\\output\\12_rendered.png', '.\\output\\13_rendered.png', '.\\output\\2_rendered.png',
                '.\\output\\3_rendered.png', '.\\output\\4_rendered.png', '.\\output\\5_rendered.png',
                '.\\output\\6_rendered.png', '.\\output\\7_rendered.png', '.\\output\\8_rendered.png',
                '.\\output\\9_rendered.png']
    fs = ('E:\\Python\\temp\\code38\\1.jpg',
          'E:\\Python\\temp\\code38\\10.png',
          'E:\\Python\\temp\\code38\\11.jpg',
          'E:\\Python\\temp\\code38\\12.jpg',
          'E:\\Python\\temp\\code38\\13.png',
          'E:\\Python\\temp\\code38\\2.jpg',
          'E:\\Python\\temp\\code38\\3.png',
          'E:\\Python\\temp\\code38\\4.jpg',
          'E:\\Python\\temp\\code38\\5.jpg',
          'E:\\Python\\temp\\code38\\6.jpg',
          'E:\\Python\\temp\\code38\\7.jpg',
          'E:\\Python\\temp\\code38\\8.jpg',
          'E:\\Python\\temp\\code38\\9.png')

    # from bodyfeature import *
    from matplotlib import pyplot as plt

    i = 9
    self = pose = Pose(jsonfs[i])


    def show(f1, f2):
        plt.subplot(1, 2, 1)
        plt.imshow(plt.imread(f1))
        plt.subplot(1, 2, 2)
        plt.imshow(plt.imread(f2))
        plt.show()


    show(fs[i], renderfs[i])
    pose.body.is_raise()
