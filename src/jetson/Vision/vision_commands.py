import ev3control.master as master
import Vision.frcnn
import cv2
from ev3control.messages import *

class VisualFeedback():

    def __init__(self):
        self._distance = None
        self._angle = None
        self._class_name = None
        self._uuid = None

    def get_distance(self):
        return self._distance

    def set_distance(self,value):
        self._distance = value

    distance = property(get_distance,set_distance,'distance')


    def get_angle(self):
        return self._angle

    def set_angle(self,value):
        self._angle = value

    angle = property(get_angle,set_angle,'angle')

    def get_class_name(self):
        return self._class_name

    def set_class_name(self,value):
        self._class_name = value

    class_name = property(get_class_name,set_class_name,'class_name')

    """
    def get_uuid(self):
        return self._uuid

    def set_uuid(self,value):
        self._uuid = value

    uuid = property(get_uuid,set_uuid,'uuid')

    """


def grab_camera_image(camera_sensor):

    return camera_sensor.read()['onBoardCamera']


def addVisionDevices(client,topic,qos=2):
    
    master.publish_cmd(client, topic, AddDeviceMessage('Vision', "VisualFeedback()"),delay=1,qos=qos)


def get_bbox(key_tuple):

    return key_tuple[1]

def get_distance(key_tuple):

    return key_tuple[2]

def get_angle(key_tuple):

    return key_tuple[3]

def get_class_name(key_tuple):

    return key_tuple[0]


def analyse_image(predictor,img):

    ret_val = predictor.detect_known_objects(img)
    info = []
    for i in range(len(ret_val)):
        class_name = "object_"+get_class_name(ret_val[i])
        bbox = get_bbox(ret_val[i]) 
        distance = get_distance(ret_val[i])
        angle = get_angle(ret_val[i])
        #Add bbox??
        info.append((class_name,distance,angle))

    return info
 

def publish_vision_info(client,topic,info):
#Use same device name as in vision_commands.py
    master.publish_cmd(client,topic, SetAttrMessage('Vision','class_name',repr(info[0])),qos=2)  
    master.publish_cmd(client,topic, SetAttrMessage('Vision','distance',repr(info[1])),qos=2) #do we care about quality of service here??? probably not,want speed
    master.publish_cmd(client,topic, SetAttrMessage('Vision','angle',repr(info[2])),qos=2)
    

def save_image(img_name,img,info):

    bbox = info[0]
    (real_x1, real_y1, real_x2, real_y2) = bbox
    cv2.rectangle(img,(real_x1, real_y1), (real_x2, real_y2), (0,0,255),5)
    cv2.imwrite(img_name,img)


def see_and_tell(predictor, client, topic, img, img_name="./test_see_tell.jpg"):

    info = analyse_image(predictor,img)
    for i in info:
        publish_vision_info(client,topic,i)
        #save_image(img_name,img,info)
