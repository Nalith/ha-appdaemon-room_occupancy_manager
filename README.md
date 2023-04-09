# Room Occupancy Manager

## Introduction

This repository contains a Python script that helps to manage the occupancy of a room using various types of sensors, such as motion sensors, door sensors, light sensors, vibration sensors, and power usage sensors. The script was created using ChatGPT-4, a large language model developed by OpenAI. The purpose of the Room Occupancy Manager is to automate the process of turning on and off lights based on the room's occupancy, time of day, sun elevation, and other factors, providing a more energy-efficient and convenient lighting control system.

## Home Assistant Components

The Room Occupancy Manager script requires the following Home Assistant components to work properly:

1. [Binary Sensor](https://www.home-assistant.io/integrations/binary_sensor/): For motion sensors, door sensors, and vibration sensors.
2. [Sensor](https://www.home-assistant.io/integrations/sensor/): For power usage sensors and the sun elevation sensor.
3. [Light](https://www.home-assistant.io/integrations/light/): For controlling the lights in the room.
4. [Weather](https://www.home-assistant.io/integrations/weather/): For getting the current weather condition, if desired.
5. [Sun](https://www.home-assistant.io/integrations/sun/): For getting the sun elevation data.
6. [Zone](https://www.home-assistant.io/integrations/zone/): For determining the home location (latitude and longitude) to calculate the current season.
7. [Timer](https://www.home-assistant.io/integrations/timer/): For managing the room occupancy timer.

## Overview

The script is designed to work with the AppDaemon platform, which allows you to run Python apps that interact with the Home Assistant automation platform. The Room Occupancy Manager script provides a class called `RoomOccupancyManager` that inherits from `hass.Hass`. This class contains various methods for handling sensor events and automating light control.

The main features of the Room Occupancy Manager include:

- Turning on lights when motion is detected: The script listens for motion sensor events and turns on the lights when motion is detected in the room.
- Turning on lights when a door is opened (configurable): If configured, the script will also turn on the lights when a door sensor indicates that the door has been opened.
- Turning on lights when the sun elevation is below a configurable threshold: The script checks the sun's elevation and turns on the lights when the elevation is below the specified threshold. This ensures that the lights are only turned on when natural lighting is insufficient.
- Adjusting the sun elevation threshold based on the current season: The script calculates the current season based on the home's latitude and adjusts the sun elevation threshold accordingly. This takes into account the seasonal changes in sunlight availability.
- Turning on lights when the weather is rainy or pouring (configurable): If configured, the script will turn on the lights when the weather entity indicates that it is raining or pouring outside, providing better lighting conditions during poor weather.
- Turning off lights when the room is unoccupied for a certain amount of time: The script utilizes a timer that is reset every time a relevant sensor event occurs (e.g., motion detected, door opened, etc.). If the timer expires without any new sensor events, the script assumes that the room is unoccupied and turns off the lights.
- Overriding the light automation with a manual control: The script allows for a manual override of the automated light control. When the override is active, the lights can be controlled manually without being affected by the automation.

## Usage

1. Install AppDaemon following the official [AppDaemon installation instructions](https://appdaemon.readthedocs.io/en/latest/INSTALL.html).
2. Clone this repository or copy the `room_occupancy_manager.py` script to your AppDaemon apps folder.
3. Configure the script in your `apps.yaml` file, providing the required parameters (motion sensors, door sensors, light sensors, etc.).
4. Start AppDaemon and ensure the Room Occupancy Manager app is running.

## Acknowledgements

This script was created using ChatGPT-4, a large language model developed by OpenAI. I would like to express my gratitude to the OpenAI team for providing this powerful AI tool that helped me in the creation of this automation script.

## License

This project is licensed under the MIT License. Please see the [LICENSE](LICENSE) file for details.
