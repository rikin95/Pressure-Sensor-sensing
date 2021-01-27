#!/usr/bin/env python

from __future__ import print_function

# Read button input through a CD4021 shift register

# Thanks to WiringPi,
# https://github.com/WiringPi/WiringPi/blob/9a8f8bee5df60061645918231110a7c2e4d3fa6b/devLib/piNes.c

import RPi.GPIO as GPIO
import time
import tkinter as tk
import math


GPIO.setwarnings(False)
class CD4021:
    pulse_time = .000025     # gordonDrogon says 25 microseconds, .000025
    
    global totalbits
    totalbits = 8
    def __init__(self, clock, latch, data, num_chips=1):
        self.latch = latch   # aka M on the pinout, pin 9
        self.clock = clock   # aka CLK, pin 10
        self.data = data     # data out, pin 3, labeled as Q7 or Q8
        # pinout diagrams seem to vary on how they number the Q pins:
        # the pins all send out the same data but the early Qs are one
        # and two clock pulses behind the biggest Q, which should be
        # on pin 3. So use that one.

        self.num_chips = num_chips

        GPIO.setup(self.latch, GPIO.OUT)
        GPIO.setup(self.clock, GPIO.OUT)
        GPIO.setup(self.data, GPIO.IN)

       
    def pulse_pin(self, pin):
        '''Pulse a pin high, then low'''
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(CD4021.pulse_time)
        GPIO.output(pin, GPIO.LOW)
        # time.sleep(CD4021.pulse_time)

    def read_shift_regs(self):
        '''Read the results of the shift registers.
           Returns a list of bytes, one for each chip.
        '''
        bytelist = []

        # Toggle Latch - which presents the first bit
        self.pulse_pin(self.latch)

        for i in range(self.num_chips):
            value = GPIO.input(self.data)
            # Now get the rest of the bits with the clock
            for i in range(totalbits-1):
                self.pulse_pin(self.clock)
                value = (value << 1) | GPIO.input(self.data)

            bytelist.append(value)
            self.pulse_pin(self.clock)
            # XXX This means one extra clock pulse at the end of
            # all the reading, but I think that'll be okay.

        return bytelist

    # XXX Should remove read_*byte* after verifying that read_shift_regs
    # works okay for keyboard.py.
    def read_byte(self):
        # Read first bit
        value = GPIO.input(self.data)

        # Now get the rest of the bits with the clock
        for i in range(totalbits-1):
            self.pulse_pin(self.clock)
            value = (value << 1) | GPIO.input(self.data)

        return value

    def read_one_byte(self):
        # Toggle Latch - which presents the first bit
        self.pulse_pin(self.latch)

        return self.read_byte()

    def read_n_bytes(self, numbytes):
        bytesread = [ self.read_one_byte() ]

        for i in range(1, numbytes):
            # For subsequent bytes, we don't want another latch but
            # read_byte doesn't start with a clock pulse, so do it here.
            self.pulse_pin(self.clock)
            bytesread.append(self.read_byte())

        return bytesread

root= tk.Tk()
canvas = tk.Canvas(root, bg='white', width=1500, height=1500)
canvas.grid()

if __name__ == '__main__':
    # Use GPIO numbering:
    GPIO.setmode(GPIO.BCM)    

    # Python has no native way to print binary unsigned numbers. Lame!
    def tobin(data, width=totalbits):
        data_str = bin(data & (2**width-1))[2:].zfill(width)
        return data_str

    shiftr = CD4021(clock=4, latch=3, data=2, num_chips=1)
    # For compatibility with SN74LS165 examples and SPI attempts:
    # shiftr = CD4021(clock=11, latch=7, data=9, num_chips=1)
    try:
        while True:
            # bytelist = [ shiftr.read_one_byte() ]
            # bytelist = shiftr.read_n_bytes(3)
            bytelist = shiftr.read_shift_regs()
            print(bytelist)
            print('   '.join([tobin(b, totalbits) for b in bytelist]))
            #print('   '.join(["%16x" % b for b in bytelist]))
            marginTop = 5
            marginLeft = 5
            itemsInRow = 3
            startX = 5
            startY = 5
            rX = startX
            rY = startY
            rHeight = 50
            rWidth = 50
            rMargin = 10
            startTextX = 25
            startTextY = 25
            textY = startTextY
            textX = startTextX
            totalSensors = totalbits
            itemsInCurrentRow = totalSensors if totalSensors < itemsInRow else itemsInRow
            itemsLeft = totalSensors - itemsInRow
            rows = 6
            column =  (totalSensors/18) if (totalSensors/18) == int else math.ceil(totalSensors/18) + 1
            pressedCount = 0
            sensorCount = 0
            for data in bytelist:
                a = tobin(data, totalSensors) 
                for c in range(0, column):
                    for b in range(0 , rows):
                        for i in range(0, itemsInCurrentRow):
                            color = 'red'
                            if(a[totalSensors - 1 - i - c - b * itemsInRow] == "1"):
                                color = 'green'
                                pressedCount = pressedCount + 1
                            sensorCount = sensorCount + 1
                            canvas.create_rectangle(rX, rY, rX + rWidth, rY + rHeight, width=0, fill=color)
                            rX = rX + rMargin + rWidth
                            canvas.create_text(textX, textY, text='S-' + str(sensorCount),fill= 'white', width= 0)
                            textX = textX + (rWidth + rMargin)

                        itemsInCurrentRow = itemsLeft if itemsLeft <= itemsInRow else itemsInRow
                        itemsLeft = itemsLeft - itemsInRow
                        rX = startX if c <= 0 else rX - rMargin * 3 - rWidth * 3
                        rY = rY + rHeight + rMargin
                        
                        textX = startTextX if c <= 0 else textX - rMargin * 3 - rWidth * 3
                        textY = textY + (rHeight + rMargin)
                    
                    itemsInCurrentRow = itemsLeft if itemsLeft < itemsInRow else itemsInRow
                    totalSensors = itemsLeft + 4 
                    rX = rX + rMargin * 3 + rWidth * 3
                    rY = startY
                    textX = textX + rMargin * 3 + rWidth * 3
                    textY = startTextY   

            print('S_total =', pressedCount)
            
            
            #canvas.create_text(120, 375, text='>>> Pressure pad ' + str(pressedCount/totalbits * 100) + '% full',fill= 'black', width= 0)

  
            root.update_idletasks()
            root.update()  
            time.sleep(0.000025)
    except KeyboardInterrupt:
        GPIO.cleanup()
