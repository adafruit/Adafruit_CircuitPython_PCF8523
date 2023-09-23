# SPDX-FileCopyrightText: 2016 Philip R. Moyer for Adafruit Industries
# SPDX-FileCopyrightText: 2016 Radomir Dopieralski for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Bernhard Bablok
#
# SPDX-License-Identifier: MIT

"""
`timer` - PCF8523 Timer module
==============================

This class supports the timer of the PCF8523-based RTC in CircuitPython.

Functions are included for reading and writing registers and manipulating
timer objects.

The class supports stand-alone usage. In this case, pass an i2-bus object
to the constructor. If used together with the PCF8523 class (rtc), instantiate
the rtc-object first and then pass the i2c_device attribute of the rtc
to the constructor of the timer.

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
from adafruit_register import i2c_bit
from adafruit_register import i2c_bits
from micropython import const

try:
    import typing import Union
    from busio import I2C
except ImportError:
    pass


class Timer:  # pylint: disable=too-few-public-methods
    """Interface to the timer of the PCF8563 RTC.

    :param I2C i2c_bus: The I2C bus object
    """

    timerA_enabled = i2c_bits.RWBits(2, 0x0F, 1)
    """Configures timerA. Possible values:
    00 - disabled
    01 - enabled as countdown timer
    10 - enabled as watchdog timer
    11 - disabled
    """

    timerA_frequency = i2c_bits.RWBits(3, 0x10, 0)
    """TimerA clock frequency. Default is 1/3600Hz.
    Possible values are as shown (selection value - frequency).
    000 - 4.096kHz
    001 - 64Hz
    010 -  1Hz
    011 -  1/60Hz
    111 -  1/3600Hz
    """

    TIMER_FREQ_4KHZ = const(0b000)
    """Timer frequency of 4 KHz"""
    TIMER_FREQ_64HZ = const(0b001)
    """Timer frequency of 64 Hz"""
    TIMER_FREQ_1HZ = const(0b010)
    """Timer frequency of 1 Hz"""
    TIMER_FREQ_1_60HZ = const(0b011)
    """Timer frequency of 1/60 Hz"""
    TIMER_FREQ_1_3600HZ = const(0b111)
    """Timer frequency of 1/3600 Hz"""

    timerA_value = i2c_bits.RWBits(8, 0x11, 0)
    """ TimerA value (0-255). The default is undefined.
    The total countdown duration is calcuated by
    timerA_value/timerA_frequency. For a higher precision, use higher values
    and frequencies, e.g. for a one minute timer you could use
    value=1, frequency=1/60Hz or value=60, frequency=1Hz. The
    latter will give better results. See the PCF85x3 User's Manual
    for details."""

    timerA_interrupt = i2c_bit.RWBit(0x01, 1)
    """True if the interrupt pin will assert when timerA has elapsed.
    Defaults to False."""

    timerA_watchdog = i2c_bit.RWBit(0x01, 2)
    """True if the interrupt pin will output when timerA generates a
    watchdog-alarm. Defaults to False."""

    timerA_status = i2c_bit.RWBit(0x01, 6)
    """True if timerA has elapsed. Set to False to reset."""

    timerA_pulsed = i2c_bit.RWBit(0x0F, 7)
    """True if timerA asserts INT as a pulse. The default
    value False asserts INT permanently."""

    timerB_enabled = i2c_bit.RWBit(0x0F, 0)
    """True if the timerB is enabled. Default is False."""

    timerB_frequency = i2c_bits.RWBits(3, 0x12, 0)
    """TimerB clock frequency. Default is 1/3600Hz.
    Possible values are as shown (selection value - frequency).
    000 - 4.096kHz
    001 - 64Hz
    010 -  1Hz
    011 -  1/60Hz
    111 -  1/3600Hz
    """

    timerB_value = i2c_bits.RWBits(8, 0x13, 0)
    """ TimerB value (0-255). The default is undefined.
    The total countdown duration is calcuated by
    timerB_value/timerB_frequency. For a higher precision, use higher values
    and frequencies, e.g. for a one minute timer you could use
    value=1, frequency=1/60Hz or value=60, frequency=1Hz. The
    latter will give better results. See the PCF85x3 User's Manual
    for details."""

    timerB_interrupt = i2c_bit.RWBit(0x01, 0)
    """True if the interrupt pin will assert when timerB has elapsed.
    Defaults to False."""

    timerB_status = i2c_bit.RWBit(0x01, 5)
    """True if timerB has elapsed. Set to False to reset."""

    timerB_pulsed = i2c_bit.RWBit(0x0F, 6)
    """True if timerB asserts INT as a pulse. The default
    value False asserts INT permanently."""

    def __init__(self, i2c: Union[I2C, I2CDevice]) -> None:
        if isinstance(i2c, I2CDevice):
            self.i2c_device = i2c  # reuse i2c_device (from PCF8523-instance)
        else:
            time.sleep(0.05)
            self.i2c_device = I2CDevice(i2c, 0x68)
