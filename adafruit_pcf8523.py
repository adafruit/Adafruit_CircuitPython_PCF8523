# SPDX-FileCopyrightText: 2016 Philip R. Moyer for Adafruit Industries
# SPDX-FileCopyrightText: 2016 Radomir Dopieralski for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pcf8523` - PCF8523 Real Time Clock module
====================================================

This library supports the use of the PCF8523-based RTC in CircuitPython. It
contains a base RTC class used by all Adafruit RTC libraries. This base
class is inherited by the chip-specific subclasses.

Functions are included for reading and writing registers and manipulating
datetime objects.

Author(s): Philip R. Moyer and Radomir Dopieralski for Adafruit Industries.
Date: November 2016
Affiliation: Adafruit Industries

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
#. Datasheet: http://cache.nxp.com/documents/data_sheet/PCF8523.pdf

"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PCF8523.git"

from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register import i2c_bit
from adafruit_register import i2c_bits
from adafruit_register import i2c_bcd_alarm
from adafruit_register import i2c_bcd_datetime

try:
    import typing  # pylint: disable=unused-import
    from busio import I2C
    from time import struct_time
except ImportError:
    pass

STANDARD_BATTERY_SWITCHOVER_AND_DETECTION = 0b000
BATTERY_SWITCHOVER_OFF = 0b111


class PCF8523:
    """Interface to the PCF8523 RTC.

    :param ~busio.I2C i2c_bus: The I2C bus the device is connected to

    **Quickstart: Importing and using the device**

        Here is an example of using the :class:`PCF8523` class.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import time
            import board
            import adafruit_pcf8523

        Once this is done you can define your `board.I2C` object and define your sensor object

        .. code-block:: python

            i2c = board.I2C()  # uses board.SCL and board.SDA
            rtc = adafruit_pcf8523.PCF8523(i2c)

        Now you can give the current time to the device.

        .. code-block:: python

            t = time.struct_time((2017, 10, 29, 15, 14, 15, 0, -1, -1))
            rtc.datetime = t

        You can access the current time accessing the :attr:`datetime` attribute.

        .. code-block:: python

            current_time = rtc.datetime

    """

    lost_power = i2c_bit.RWBit(0x03, 7)
    """True if the device has lost power since the time was set."""

    power_management = i2c_bits.RWBits(3, 0x02, 5)
    """Power management state that dictates battery switchover, power sources
    and low battery detection. Defaults to BATTERY_SWITCHOVER_OFF (0b000)."""

    # The False means that day comes before weekday in the registers. The 0 is
    # that the first day of the week is value 0 and not 1.
    datetime_register = i2c_bcd_datetime.BCDDateTimeRegister(0x03, False, 0)
    """Current date and time."""

    clockout_frequency = i2c_bits.RWBits(3, 0x0F, 3)
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

    # The False means that day and weekday share a register. The 0 is that the
    # first day of the week is value 0 and not 1.
    alarm = i2c_bcd_alarm.BCDAlarmTimeRegister(
        0x0A, has_seconds=False, weekday_shared=False, weekday_start=0
    )
    """Alarm time for the first alarm."""

    alarm_interrupt = i2c_bit.RWBit(0x00, 1)
    """True if the interrupt pin will output when alarm is alarming."""

    alarm_status = i2c_bit.RWBit(0x01, 3)
    """True if alarm is alarming. Set to False to reset."""

    battery_low = i2c_bit.ROBit(0x02, 2)
    """True if the battery is low and should be replaced."""

    high_capacitance = i2c_bit.RWBit(0x00, 7)
    """True for high oscillator capacitance (12.5pF), otherwise lower (7pF)"""

    calibration_schedule_per_minute = i2c_bit.RWBit(0x0E, 7)
    """False to apply the calibration offset every 2 hours (1 LSB = 4.340ppm);
    True to offset every minute (1 LSB = 4.069ppm).  The default, False,
    consumes less power.  See datasheet figures 28-31 for details."""

    calibration = i2c_bits.RWBits(  # pylint: disable=unexpected-keyword-arg
        7, 0xE, 0, signed=True
    )
    """Calibration offset to apply, from -64 to +63.  See the PCF8523 datasheet
    figure 18 for the offset calibration calculation workflow."""

    def __init__(self, i2c_bus: I2C):
        self.i2c_device = I2CDevice(i2c_bus, 0x68)

        # Try and verify this is the RTC we expect by checking the timer B
        # frequency control bits which are 1 on reset and shouldn't ever be
        # changed.
        buf = bytearray(2)
        buf[0] = 0x12
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)

        if (buf[1] & 0b00000111) != 0b00000111:
            raise ValueError("Unable to find PCF8523 at i2c address 0x68.")

    @property
    def datetime(self) -> struct_time:
        """Gets the current date and time or sets the current date and time then starts the
        clock."""
        return self.datetime_register

    @datetime.setter
    def datetime(self, value: struct_time):
        # Automatically sets lost_power to false.
        self.power_management = STANDARD_BATTERY_SWITCHOVER_AND_DETECTION
        self.datetime_register = value
