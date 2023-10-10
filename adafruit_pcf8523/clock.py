# SPDX-FileCopyrightText: 2016 Philip R. Moyer for Adafruit Industries
# SPDX-FileCopyrightText: 2016 Radomir Dopieralski for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Bernhard Bablok
#
# SPDX-License-Identifier: MIT

"""
`clock` - PCF8523 Clock module
==============================

This class supports the clkout-feature of the PCF8523-based RTC in CircuitPython.

Functions are included for reading and writing registers to configure
clklout frequency.

The class supports stand-alone usage. In this case, pass an i2-bus object
to the constructor. If used together with the PCF8523 class (rtc), instantiate
the rtc-object first and then pass the i2c_device attribute of the rtc
to the constructor of the clock.

Author(s): Bernhard Bablok
Date: September 2023

Implementation Notes
--------------------

**Hardware:**

* Adafruit `Adalogger FeatherWing - RTC + SD Add-on <https://www.adafruit.com/products/2922>`_
  (Product ID: 2922)
* Adafruit `PCF8523 RTC breakout <https://www.adafruit.com/products/3295>`_ (Product ID: 3295)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

**Notes:**

#. Milliseconds are not supported by this RTC.
#. The alarm does not support seconds. It will always fire on full minutes.
#. Datasheet: http://cache.nxp.com/documents/data_sheet/PCF8523.pdf

"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PCF8523.git"

import time

from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register import i2c_bits
from micropython import const

try:
    from typing import Union
    from busio import I2C
except ImportError:
    pass


class Clock:  # pylint: disable=too-few-public-methods
    """Interface to the clkout of the PCF8523 RTC.

    :param I2C i2c_bus: The I2C bus object
    """

    clockout_frequency = i2c_bits.RWBits(3, 0x0F, 3)  # COF[2:0]
    """Clock output frequencies generated. Default is 32.768kHz.
    Possible values are as shown (selection value - frequency).
    000 - 32.768khz
    001 - 16.384khz
    010 - 8.192kHz
    011 - 4.096kHz
    100 - 1.024kHz
    101 - 0.032kHz (32Hz)
    110 - 0.001kHz (1Hz)
    111 - Disabled
    """

    CLOCKOUT_FREQ_32KHZ = const(0b000)
    """Clock frequency of 32 KHz"""
    CLOCKOUT_FREQ_16KHZ = const(0b001)
    """Clock frequency of 16 KHz"""
    CLOCKOUT_FREQ_8KHZ = const(0b010)
    """Clock frequency of  8 KHz"""
    CLOCKOUT_FREQ_4KHZ = const(0b011)
    """Clock frequency of  4 KHz"""
    CLOCKOUT_FREQ_1KHZ = const(0b100)
    """Clock frequency of  4 KHz"""
    CLOCKOUT_FREQ_32HZ = const(0b101)
    """Clock frequency of 32 Hz"""
    CLOCKOUT_FREQ_1HZ = const(0b110)
    """Clock frequency of 1 Hz"""
    CLOCKOUT_FREQ_DISABLED = const(0b111)
    """Clock output disabled"""

    def __init__(self, i2c: Union[I2C, I2CDevice]) -> None:
        if isinstance(i2c, I2CDevice):
            self.i2c_device = i2c  # reuse i2c_device (from PCF8563-instance)
        else:
            time.sleep(0.05)
            self.i2c_device = I2CDevice(i2c, 0x68)
