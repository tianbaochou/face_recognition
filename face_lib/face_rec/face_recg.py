import tensorflow as tf

from face_lib.face_rec.nn import inference
from face_lib.util import utils


class Recognize:
    def __init__(self, margin=0.3):
        self.margin = margin        # 阈值
        self.siamese = inference.Siamese(96)
        self.sess = tf.Session()
        self.my_faces_path = './faces/'                  # 人脸数据集目录
        self.model_ckpt = 'model/train_faces.model'      # 模型存放目录
        self.saver = tf.train.Saver()
        self.saver.restore(self.sess, self.model_ckpt)   # 加载模型
        self.max_num = 0
        self.names = None
        self.face_array = None

    def reload_data(self):
        self.max_num, self.names, self.face_array = utils.get_triplet_data(self.my_faces_path)            # 加载人脸数据集

    def whose_face(self, test_data):
        face = [[] for n in range(self.max_num)]
        print('max num: ', self.max_num)
        for i in range(self.max_num):
            for j, img in enumerate(self.face_array[i]): # 同该person下的所有人脸进行比对
                res = self.sess.run(self.siamese.look_like, feed_dict={
                    self.siamese.x1: [test_data],
                    self.siamese.x2: [img],
                    self.siamese.keep_f: 1.0})
                face[i].append(res)
        return face

    def get_face_id(self, face):
        try:
            new_list = []
            #print('faces: ', face)
            for i in range(self.max_num):
                face[i].sort()               # 排序
                new_list.append(face[i][0])
            min_data = min(new_list)
            if min_data < self.margin:       # 阈值为0.3
                face_id = new_list.index(min_data)
            else:
                face_id = None
            return face_id, min_data
        except:
            return None, None
