import sys
import time
import cv2
import os
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from PyQt5 import QtWidgets, QtCore, QtGui
from face_lib.face_rec import face_recg
from face_lib.face_rec.face_detector import detector
from gui import Ui_widget



class MyDesignerShow(QtWidgets.QWidget, Ui_widget):
    _signal = QtCore.pyqtSignal(int)

    def __init__(self):
        super(MyDesignerShow, self).__init__()
        self.timer_camera = QtCore.QTimer()   # 本地摄像头定时器
        self.timer_udp_video = QtCore.QTimer()  # UDP获取视频定时器
        self.cap = cv2.VideoCapture()         # 获得摄像头对象
        self.CAM_NUM = 0                      # 获取摄像头编号
        self.time = time                      # 获取时间对象
         # 关键点提取模型路径
        self.PREDICTOR_PATH = './model/shape_predictor_68_face_landmarks.dat'
        self.dlib_detector = detector.AlignDlib(self.PREDICTOR_PATH)     # 获取人脸对齐对象
        self.pix = QtGui.QPixmap()            # 获取QPixmap对象
        self.pic_show = None                  # 显示的当前摄像头画面
        self.face_photo = None                # 人脸图片(最大的人脸图)
        self.face_collected = False           # 用于建立数据集的人脸图
        self.pause = False                    # 是否暂停所有检测任务
        self.is_face_recog = 0                # 是否进行人脸识别
        self.is_notify = False                # 是否提醒增加人脸数据
        self.is_show_landmarks = 0        # 是否显示landmarks
        self.face_recog = face_recg.Recognize()  # 获取人脸识别对象
        self.font = ImageFont.truetype('./fonts/simsun.ttc', 16)

        self.face_recog.reload_data()  # 重载人脸数据集

        self.setupUi(self)                          # 加载窗体
        self.btn_close.clicked.connect(self.close)   # 关闭程序
        self.btn_local_camera.clicked.connect(self.get_local_camera)      # 打开本地相机
        self.btn_get_face.clicked.connect(self.collect_face)              # 得到人脸图像
        self.btn_show_landmarks.clicked.connect(self.show_landmarks)
        self.btn_new_face.clicked.connect(self.add_face)                  # 新建人脸数据
        self.btn_face_recognize.clicked.connect(self.face_recognize)      # 人脸识别

        self.timer_camera.timeout.connect(self.show_local_camera)  # 计时结束调用show_camera()方法
        self.timer_udp_video.timeout.connect(self.show_udp_video)  # 计时结束调用show_udp_video()方法

        self.btn_status = {'btn_landmarks':[u'显示关键点', u'关闭关键点'],
                          'btn_face_reco':[u'开启人脸识别', u'关闭人脸识别'],
                          'btn_face_dete':[u'开启摄像头', u'关闭摄像头']}

    # 获取本地摄像头视频
    def get_local_camera(self):
        if self.timer_udp_video.isActive():      # 查询网络摄像头是否打开
            QtWidgets.QMessageBox.warning(self, u"Warning", u"请先关闭网络摄像头", buttons=QtWidgets.QMessageBox.Ok,
                                          defaultButton=QtWidgets.QMessageBox.Ok)

        elif not self.timer_camera.isActive():
            flag = self.cap.open(self.CAM_NUM)
            if not flag:
                QtWidgets.QMessageBox.warning(self, u"Warning", u"请检测相机与电脑是否连接正确", buttons=QtWidgets.QMessageBox.Ok,
                                                defaultButton=QtWidgets.QMessageBox.Ok)
            else:
                self.timer_camera.start(30)     # 30ms刷新一次
                self.btn_local_camera.setText(u'关闭本地摄像头')

        else:
            self.timer_camera.stop()    # 定时器关闭
            self.cap.release()          # 摄像头释放
            self.label_camera.clear()   # 视频显示区域清屏
            self.graphicsView.show()
            self.btn_local_camera.setText(u'打开本地摄像头')

    def show_local_camera(self):
        """
        显示本地摄像头
        """
        flag, image = self.cap.read() # 读取摄像头数据
        self.pic_show = cv2.resize(image, (640, 480)) #
        self.pic_show = self.detection() # 在图像中显示人脸
        self.pic_show = cv2.cvtColor(self.pic_show, cv2.COLOR_BGR2RGB) # QT中以RGB形式显示
        showimage = QtGui.QImage(self.pic_show.data, self.pic_show.shape[1], self.pic_show.shape[0], QtGui.QImage.Format_RGB888)
        self.graphicsView.close()
        self.label_camera.setPixmap(self.pix.fromImage(showimage))     # 实时显示摄像头图像+检测
        if self.face_photo is None:
            return
        face_photo = cv2.cvtColor(self.face_photo, cv2.COLOR_BGR2RGB)
        face_photo = QtGui.QImage(face_photo.data, face_photo.shape[1], face_photo.shape[0], QtGui.QImage.Format_RGB888)
        self.label_face.setPixmap(QtGui.QPixmap.fromImage(face_photo)) #  显示截取的最大人脸框


    def get_udp_video(self):
        if self.timer_camera.isActive():      # 查询本地摄像头
            QtWidgets.QMessageBox.warning(self, u"Warning", u"请先关闭本地摄像头", buttons=QtWidgets.QMessageBox.Ok,
                                          defaultButton=QtWidgets.QMessageBox.Ok)
        elif not self.timer_udp_video.isActive():
            self.time.sleep(1)
            self.udp_video = UdpGetVideo()  # 获取udp视频对象
            self.timer_udp_video.start(30)     # 10ms刷新一次
            self.btn_web_camera.setText(u'关闭网络摄像头')

        else:
            self.timer_udp_video.stop()    # 定时器关闭
            self.udp_video.close()         # udp视频接受关闭
            self.label_camera.clear()      # 视频显示区域清屏
            self.graphicsView.show()
            self.btn_web_camera.setText(u'打开网络摄像头')

    def show_udp_video(self):

        image = self.udp_video.receive()
        # 从内存缓存区中读取图像
        decimg = cv2.imdecode(image, 1)
        self.pic_show = cv2.resize(decimg, (640, 480))
        self.pic_show = cv2.cvtColor(self.pic_show, cv2.COLOR_BGR2RGB)
        showimage = QtGui.QImage(self.pic_show.data, self.pic_show.shape[1], self.pic_show.shape[0], QtGui.QImage.Format_RGB888)
        self.graphicsView.close()
        self.label_camera.setPixmap(self.pix.fromImage(showimage))

    def detection(self):
        """
        获取人脸图像
        """
        # 确定摄像头已经打开了
        flag_cam = True
        if not self.timer_camera.isActive() and not self.timer_udp_video.isActive():      # 查询摄像头是否开启
            QtWidgets.QMessageBox.warning(self, u"Warning", u"请先打开摄像头", buttons=QtWidgets.QMessageBox.Ok,
                                          defaultButton=QtWidgets.QMessageBox.Ok)
            flag_cam = False

        if flag_cam:
            # 处于输入姓名阶段
            if self.pause:
                return self.pic_show

            pic = self.pic_show
            if pic is not None:
                # 使用dlib自带的frontal_face_detector作为我们的特征提取器
                biggest_idx, faces_rect, faces_align, landmarks = self.dlib_detector.align(96, pic)
                if faces_align is None: # 没有检测到人脸
                     self.textEdit.append("没有检测到人脸!")
                else: #识别人脸、绘制人脸框、添加label
                    if self.face_collected:
                        try:
                            self.face_photo = faces_align[biggest_idx] # 将最大的人脸缓存
                            self.face_collected = False                # 关闭收集
                        except:
                            self.face_photo = None
                    names = self.face_recog.names
                    if len(names) < 1 and self.is_notify:
                        if not self.is_notify:
                            self.is_notify = True
                            QtWidgets.QMessageBox.warning(self, u"Warning", u"人脸数据集为空，请添加！", buttons=QtWidgets.QMessageBox.Ok,
                                                      defaultButton=QtWidgets.QMessageBox.Ok)
                    else:

                        for idx, f_align in enumerate(faces_align):
                            f_align = cv2.cvtColor(f_align, cv2.COLOR_RGB2BGR)
                            image_data = np.array(f_align)
                            image_data = image_data.astype('float32') / 255.0

                            # 显示 landmarks
                            if self.is_show_landmarks == 1:
                                for pidx, point in enumerate(landmarks[idx]):
                                    cv2.circle(pic,(point[0], point[1]), 1, (55, 255, 155), 1)

                            # 绘制人脸框
                            c1 = faces_rect[idx][0]
                            c2 = faces_rect[idx][1]
                            cv2.rectangle(pic, c1, c2, (255,0,0), 1)

                            # 进行人脸识别
                            if self.is_face_recog == 1:
                                recog_names = 'unknown'
                                face_like = self.face_recog.whose_face(image_data)  # 识别人脸
                                face_id, distance = self.face_recog.get_face_id(face_like)
                                if face_id is not None:
                                    recog_names = str(names[face_id])

                                # 绘制中文label
                                img_pil = Image.fromarray(pic)
                                draw = ImageDraw.Draw(img_pil)
                                t_size = draw.textsize(recog_names, font=self.font) # 获取文字大小

                                draw.text(c1, recog_names, font=self.font, fill=(0,255,0,0))
                                pic = np.array(img_pil)
                return pic
            else:
                QtWidgets.QMessageBox.warning(self, u"Warning", u"没有检测到图片", buttons=QtWidgets.QMessageBox.Ok,
                                              defaultButton=QtWidgets.QMessageBox.Ok)

    def face_recognize(self):
        self.is_face_recog = 1 if self.is_face_recog == 0 else 0
        self.btn_face_recognize.setText(self.btn_status['btn_face_reco'][self.is_face_recog])

    def show_landmarks(self):
        self.is_show_landmarks = 1 if self.is_show_landmarks == 0 else 0
        self.btn_show_landmarks.setText(self.btn_status['btn_landmarks'][self.is_show_landmarks])

    def collect_face(self):
        self.face_collected = True

    def add_face(self):
        self.pause = True

        # 检查是否已经有人脸图像在缓存中
        if self.face_photo is  None:
            QtWidgets.QMessageBox.warning(self, u"Warning", u"请先点击获取人脸", buttons=QtWidgets.QMessageBox.Ok,
                                          defaultButton=QtWidgets.QMessageBox.Ok)
            self.pause = False
            return

        text, ok = QtWidgets.QInputDialog.getText(self, '姓名不同的同学请输入不同名字!', '请输入你的名字：')
        if ok:
            print(text)
            # 创建文件夹
            paths = './faces/' + text + '/'
            if not os.path.exists(paths):
                os.makedirs(paths)
                self.textEdit.append("人脸已存放在 " + paths + ' 文件夹中！！')
            else:
                QtWidgets.QMessageBox.warning(self, u"Warning", u"数据集中已有相同人名（将为该人添加照片）！",
                                              buttons=QtWidgets.QMessageBox.Ok,
                                              defaultButton=QtWidgets.QMessageBox.Ok)
            # 保存图片
            s_time = time.ctime().replace(' ', '_').replace(':', '_')
            # save_image =  cv2.cvtColor(self.face_photo, cv2.COLOR_RGB2BGR)  # 转为BGR图片
            cv2.imencode('.jpg',self.face_photo)[1].tofile(str(paths) + str(s_time) + '.jpg')
            self.face_recog.reload_data() # 重新加载数据
            self.face_photo = None
            self.pause = False            # 重新开始检测
        else:
            QtWidgets.QMessageBox.warning(self, u"Warning", u"输入错误", buttons=QtWidgets.QMessageBox.Ok,
                                          defaultButton=QtWidgets.QMessageBox.Ok)

    def closeEvent(self, event):
        ok = QtWidgets.QPushButton()
        cacel = QtWidgets.QPushButton()

        msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, u"关闭", u"是否关闭！")

        msg.addButton(ok, QtWidgets.QMessageBox.ActionRole)
        msg.addButton(cacel, QtWidgets.QMessageBox.RejectRole)
        ok.setText(u'确定')
        cacel.setText(u'取消')
        if msg.exec_() == QtWidgets.QMessageBox.RejectRole:
            event.ignore()
        else:
            if self.cap.isOpened():
                self.cap.release()
            if self.timer_camera.isActive():
                self.timer_camera.stop()
            if self.timer_udp_video.isActive():
                self.timer_udp_video.stop()
            event.accept()

if __name__ == "__main__":
    if not os.path.exists("./faces"):
        os.makedirs("./faces")
    app = QtWidgets.QApplication(sys.argv)
    myshow = MyDesignerShow()    # 创建实例
    myshow.show()                # 使用Qidget的show()方法
    sys.exit(app.exec_())
