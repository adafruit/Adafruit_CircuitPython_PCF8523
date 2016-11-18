
Introduction to Adafruit's PCF8523 Real Time Clock (RTC) Library
================================================================

This is a great battery-backed real time clock (RTC) that allows your
microcontroller project to keep track of time even if it is reprogrammed,
or if the power is lost. Perfect for datalogging, clock-building, time
stamping, timers and alarms, etc. Equipped with PCF8523 RTC - it can
run from 3.3V or 5V power & logic!

The PCF8523 is simple and inexpensive but not a high precision device.
It may lose or gain up to two seconds a day. For a high-precision,
temperature compensated alternative, please check out the
`DS3231 precision RTC. <https://www.adafruit.com/products/3013>`_
If you need a DS1307 for compatibility reasons, check out our
`DS1307 RTC breakout <https://www.adafruit.com/products/3296>`_.

.. image:: 3295-00.jpg

Implementation Details
=======================

Background
----------

This page contains the details of the functions, classes, and methods
available in the PCF8523 library.

The DS3231 library consists of three major sections:

#. Functions
#. The base class _BaseRTC
#. The subclass PCF8523

Functions
---------

The only library functions of which you need to be aware of for the
PCF8523 are datetime_tuple() and alarm_tuple().

The first is the function that creates an object
you use to set the clock time. It takes eight arguments and returns a
datetimetuple object containing the new time settings. The arguments are
positional rather than keyword arguments. They are, in order:

* Year (4-digit)
* Month (2-digit)
* Day of the month (2-digit)
* Day of the week (1 digit, 0 = Sunday)
* Hour (24 hour clock, 2-digit)
* Minute (2-digit)
* Seconds (2-digits)
* The digit 0 (representing milliseconds, which are not supported by this RTC)

The second is the function that returns an alarmtuple structure to set the
alarm on the RTC. It takes four arguments:

* Day of the week
* Day of the month
* hour
* minute

See the section, below, on usage for examples.

Class Methods
-------------

Here are the important class methods for you to know:

* datetime() - sets or returns the RTC clock time
* alarm_time() - sets or returns the current alarm setting
* _register() - returns the contents of a register in the RTC chip
* stop() - suspends RTC operation or, if the argument is None, returns the
  current setting.
* lost_power() - returns true or false depending on whether the board has
  lost power. Passing the value "False" will reset the flag.
* alarm() - returns the alarm state (True or False). Passing False as the
  argument will reset the flag.
* battery_low() - returns True if the battery voltage is low (i.e., the battery
  needs to be replaced)

Usage Notes
===========

Of course, you must import the library to use it:

   import machine

   import adafruit_pcf8523

All the Adafruit RTC libraries take an instantiated and active I2C object
(from the machine library) as an argument to their constructor. The way to
create an I2C object depends on the board you are using. If you are using the
ATSAMD21-based board, like the Feather M0, you **must** initialize the object
after you create it:

   myI2C = machine.I2C(machine.Pin('SCL'), machine.Pin('SDA'))

   myI2C.init()

If you are using the ESP8266-based boards, however, you do not need to
init() the object after creating it:

   myI2C = machine.I2C(machine.Pin(5), machine.Pin(4))

Once you have created the I2C interface object, you can use it to instantiate
the RTC object:

   rtc = adafruit_pcf8523.PCF8523(myI2C)

To set the time, you need to pass datetime() a datetimetuple object:

   newTime = adafruit_pcf8523.datetime_tuple(2016,11,18,6,9,36,0,0)

   rtc.datetime(newTime)

After the RTC is set, you retrieve the time by calling the datetime() method
without any arguments.

   curTime = rtc.datetime()

The PCF8523 supports an alarm function. You set the alarm very similarly to
the way you set the datetime.

   newAlarm = adafruit_pcf8523.alarm_tuple(6,18,10,41)

   rtc.alarm_time(newAlarm)

Also, the PCF89523 is the only RTC from Adafruit that has a low battery
detection. The battery_low() method returns True if the battery needs to be
replaced. The only way to clear the flag is to replace the CR1220 battery.

Many more details can be found in the Docs/_build directory.
