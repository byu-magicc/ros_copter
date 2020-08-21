#!/usr/bin/env python

import numpy as np
import rospy

from geometry_msgs.msg import PoseStamped
from ublox.msg import PosVelEcef
from rosflight_msgs.msg import GNSS

from mocap2ublox import Mocap2Ublox


class Mocap2UbloxROS():

    def __init__(self):

        self.load_set_parameters()

        self.m2u = Mocap2Ublox(self.Ts, self.global_horizontal_accuracy, \
            self.global_vertical_accuracy, self.global_speed_accuracy, \
            self.noise_on, self.ref_lla, self.sigma_rover_pos, \
            self.sigma_rover_vel, self.lpf_on, self.A, self.B)

        # Publishers
        self.rover_virtual_PosVelEcef_pub_ = rospy.Publisher('rover_PosVelEcef', PosVelEcef, queue_size=5, latch=True)
        
        # Subscribers
        self.rover_mocap_ned_sub_ = rospy.Subscriber('rover_mocap', PoseStamped, self.roverMocapNedCallback, queue_size=5)
        
        # Timer
        self.ublox_rate_timer_ = rospy.Timer(rospy.Duration(self.Ts), self.ubloxRateCallback)


        while not rospy.is_shutdown():
            # wait for new messages and call the callback when they arrive
            rospy.spin()


    def roverMocapNedCallback(self, msg):
        
        self.m2u.rover_ned = np.array([msg.pose.position.x,
                                   msg.pose.position.y,
                                   msg.pose.position.z])

    
    def ubloxRateCallback(self, event):
        
        #publishes all the messages together like ublox would

        #TODO use event to get time
        time_stamp = rospy.Time.now()
        current_time = time_stamp.secs+time_stamp.nsecs*1e-9
        dt = current_time - self.prev_time
        self.prev_time = current_time

        #update messages
        self.m2u.update_rover_virtual_PosVelEcef(dt)

        #publish messages
        self.publish_rover_virtual_PosVelEcef(time_stamp)


    def publish_rover_virtual_PosVelEcef(self, time_stamp):

        self.rover_PosVelEcef.header.stamp = time_stamp
        self.rover_PosVelEcef.fix = 3
        # # self.rover_PosVelEcef.lla = self.rover_lla  #lla is not currently being used            
        self.rover_PosVelEcef.position = self.m2u.rover_virtual_pos_ecef
        self.rover_PosVelEcef.horizontal_accuracy = self.global_horizontal_accuracy
        self.rover_PosVelEcef.vertical_accuracy = self.global_vertical_accuracy
        self.rover_PosVelEcef.velocity = self.m2u.rover_virtual_vel_ecef
        self.rover_PosVelEcef.speed_accuracy = self.global_speed_accuracy

        self.rover_virtual_PosVelEcef_pub_.publish(self.rover_PosVelEcef)

    
    def load_set_parameters(self):

        ublox_frequency = rospy.get_param('~ublox_frequency', 5.0)
        self.Ts = 1.0/ublox_frequency
        self.global_horizontal_accuracy = rospy.get_param('~global_horizontal_accuracy', 0.4)
        self.global_vertical_accuracy = rospy.get_param('~global_vertical_accuracy', 0.6)
        self.global_speed_accuracy = rospy.get_param('~global_speed_accuracy', 0.4)
        self.noise_on = rospy.get_param('~noise_on', True)
        ref_lla = rospy.get_param('~ref_lla', [40.267320, -111.635629, 1387.0])
        self.ref_lla = np.array(ref_lla)
        self.sigma_rover_pos = rospy.get_param('~sigma_rover_pos', 5.0) 
        self.sigma_rover_vel = rospy.get_param('~sigma_rover_vel', 5.0)
        self.sigma_rover_relpos = rospy.get_param('~sigma_rover_relpos', 0.0)
        self.lpf_on = rospy.get_param('~lpf_on', False)
        self.A = rospy.get_param('~A', 6378137.0)
        self.B = rospy.get_param('~B', 6356752.314245)

        #message types
        self.rover_PosVelEcef = PosVelEcef()

        #used for updating dt
        self.prev_time = 0.0
        

if __name__ == '__main__':
    rospy.init_node('mocap2ublox_ros', anonymous=True)
    try:
        mocap2ublox_ros = Mocap2UbloxROS()
    except:
        rospy.ROSInterruptException
    pass