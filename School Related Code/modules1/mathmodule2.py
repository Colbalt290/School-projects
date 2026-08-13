import math

def angle_demo():
    angle = math.sin(math.pi/2) #This is in radians
    print (angle)

    angle = math.sin(math.radians(90))
    print(angle)

angle_demo()

help(math)