# Room Occupancy Manager

## Introduction
The Room Occupancy Manager is an AppDaemon script designed for Home Assistant that intelligently manages room occupancy by controlling lights based on motion, door, vibration, and power usage sensors. This script offers a flexible and powerful way to automate your smart home's lighting, accounting for various conditions like weather, sunrise, and sunset times. With this script, you can enhance the responsiveness of your smart home system and create a more comfortable living environment.

## Home Assistant Components
The script interacts with several Home Assistant components, offering a versatile approach to managing room occupancy and lighting control. The components used in the script include:

- Motion sensors: Detect movement in a room and trigger the script to turn on the lights.
- Door sensors: Monitor the opening and closing of doors, allowing the script to respond accordingly.
- Light entities: Control the state of individual light entities, turning them on or off based on occupancy and other conditions.
- Vibration sensors: Detect vibrations from appliances or furniture, which may indicate room occupancy.
- Power usage sensors: Monitor the power consumption of devices in a room, providing another indicator of occupancy.
- Timer entities: Manage the duration of room occupancy and control when lights turn on and off.
- Weather entities: Respond to weather changes, adjusting lighting to suit the conditions.

## Overview
The Room Occupancy Manager script listens for changes in the state of the specified sensors and entities. When an event occurs, such as motion detected, door opened, vibration sensed, or power usage increased, the script starts a timer. While the timer is active, the lights are turned on. When the timer is idle, the lights are turned off.

The script can also account for weather conditions, like rain or pouring, adjusting the lighting accordingly. Moreover, it considers sunrise and sunset times, offering more fine-grained control over when lights are turned on. With a combination of sensors and conditions, the Room Occupancy Manager provides an efficient and intelligent way to manage your home's lighting.

## Configuration
To use the Room Occupancy Manager script, you must configure the required parameters in your `apps.yaml` file. The following example configuration demonstrates the necessary parameters and their usage:

```yaml
room_occupancy_manager:
  module: room_occupancy_manager
  class: RoomOccupancyManager
  motion_sensors:
    - binary_sensor.motion_sensor_1
    - binary_sensor.motion_sensor_2
  timer_entity: timer.room_timer
  lights:
    - light.light_1
    - light.light_2
  doors:
    - binary_sensor.door_sensor_1
    - binary_sensor.door_sensor_2
  room_occupied_on_door_open: true
  room_occupied_on_door_closed: false
  lights_always_turn_on: false
  light_override: input_boolean.light_override
  vibration_sensors:
    - binary_sensor.vibration_sensor_1
    - binary_sensor.vibration_sensor_2
  power_sensors:
    - sensor.power_sensor_1
    - sensor.power_sensor_2
  power_usage_threshold: 10
  weather_entity: weather.home
  sunrise_offset_minutes: 30
  sunset_offset_minutes: -30
