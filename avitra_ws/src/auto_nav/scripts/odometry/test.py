#!/usr/bin/env python

###################################################################################################################
# CODE TO COMPUTE ODOMETRY DATA FROM RAW ENCODER TICKS
# THE MODEL APPLIES TO DIFFERENTIAL DRIVE ROBOTS
# ODOMETRY INFORMATION IS PUBLISHED ON THE "odom" TOPIC AND ROBOT BASE MOVES WITH THE "odom" FRAME AS THE ORIGIN
# TF TREE IS BROADCAST AS FOLLOWS (laser_frame --> base_link--> odom)
###################################################################################################################

import rospy
from math import *
import tf
from nav_msgs.msg import Odometry
from auto_nav.msg import ticks_msg
from geometry_msgs.msg import Point, Pose, Quaternion, Twist, Vector3

#All in MKS
wheel_dia  = 0.154                                                                   # wheel diameter in m
ppr = 540   #135                                                                   # encoders ticks per rotation
bot_dia = 0.475
temp_distance = 0.00
angle = 0
#odom = Odometry()

##################################################################################################################

class Queue:                                                                # queue for storing published raw ticks of the encoders
    def __init__(self):
        self.items = []

    def is_empty(self):
        return self.items == []

    def enqueue(self, data):
        self.items.append(data)

    def dequeue(self):
        return self.items.pop(0)

####################################################################################################################

def ticks_callback(ticks_array):
    queue_left.enqueue(ticks_array.motor_L)
    queue_right.enqueue(ticks_array.motor_R)
    
#####################################################################################################################
if __name__ == '__main__':
    x = 0
    y = 0
    theta = 0
    angle = 0
    vx = 0.0
    vy = 0.0
    vth = 0.0
    
    
    queue_right = Queue()                                                   # queue objects for right and left encoders
    queue_left = Queue()
    
    rospy.init_node('avitra_odometry', anonymous=False)
    rospy.Subscriber("ticks", ticks_msg, ticks_callback)                # Subscribing to raw encoder tics and velocities
    
    current_time = rospy.Time.now()
    last_time = rospy.Time.now()
    dt = (current_time - last_time).to_sec()
    
    # odom_broadcaster = tf.TransformBroadcaster()
    camera_broadcaster = tf.TransformBroadcaster()
    laser_broadcaster = tf.TransformBroadcaster()
   
    #odom_pub = rospy.Publisher("odom", Odometry, queue_size=50)
    totalTicksR = 0
    totalTicksL = 0
    while not rospy.is_shutdown():
        try:
            now = rospy.Time.now()
            current_time = rospy.Time.now()
            
            if not(queue_left.is_empty()):
                ticksR = queue_right.dequeue()
                ticksL = queue_left.dequeue()
                totalTicksR += ticksR
                totalTicksL += ticksL
                # print "total ticks Left" , totalTicksL
                # print "\t"
                # print "total ticks Right" , totalTicksR
                dt = (current_time - last_time).to_sec()    # change in time
                
                theta =(ticksR-ticksL)*pi*wheel_dia/(bot_dia*ppr)                    # calculation of angular displacement from latest orientation
                angle = angle + theta                                       # absolute angular displacement
                temp_distance = ((ticksL+ticksR)/2)*pi*wheel_dia/ppr           # local linear displacemnt (from previous position)
                
                
                dx = temp_distance*cos(angle)           # change in x
                dy = temp_distance*sin(angle)           # change in y
                dth = theta                             # change in angle
                
                
                x = x + temp_distance*cos(angle)                            # absolute postions w.r.t origin
                y = y + temp_distance*sin(angle)

            odom_quat = tf.transformations.quaternion_from_euler(0, 0, angle)
            
            odom_broadcaster.sendTransform(                                                                                 # transformation of robot base_link as computed from odometry data
            (x, y, 0.),
            odom_quat,
            current_time,
            "base_link",
            "odom"
            )
            
            odom.header.stamp = current_time
            odom.header.frame_id = "odom"
            odom.child_frame_id = "base_link"
            odom.pose.pose = Pose(Point(x, y, 0.), Quaternion(*odom_quat))
            
            if dt > 0 :
                vx=dx/dt
                vy=dy/dt
                vth=dth/dt
            
            
            # odom.twist.twist = Twist(Vector3(vx, vy, 0), Vector3(0, 0, vth))
            
            # odom_pub.publish(odom)
            
            laser_broadcaster.sendTransform((0, 0, 0.35), (0, 0, 0, 1), rospy.Time.now(), "laser", "base_link")
            camera_broadcaster.sendTransform((0, 0, 0.25), (0, 0, 0, 1), rospy.Time.now(), "camera_link", "base_link")       # fixed transform between robot base and camera 
            last_time = current_time
        except Exception as E:
            print "EXCEPTION", E
            continue
