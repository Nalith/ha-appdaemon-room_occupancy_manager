import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, timedelta
import pytz

# RoomOccupancyManager class that inherits from hass.Hass
class RoomOccupancyManager(hass.Hass):

    def initialize(self):
        # Get required parameters from configuration
        self.motion_sensors = self.args["motion_sensors"]
        self.timer_entity = self.args["timer_entity"]
        self.lights = self.args["lights"]
        self.doors = self.args["doors"]
        self.room_occupied_on_door_open = self.args["room_occupied_on_door_open"]
        self.room_occupied_on_door_closed = self.args["room_occupied_on_door_closed"]
        self.lights_always_turn_on = self.args["lights_always_turn_on"]
        self.light_override = self.args["light_override"]
        self.vibration_sensors = self.args["vibration_sensors"]
        self.power_sensors = self.args["power_sensors"]
        self.power_usage_threshold = self.args["power_usage_threshold"]
        self.weather_entity = self.args["weather_entity"]
        self.sunrise_offset_minutes = self.args.get("sunrise_offset_minutes", 30)
        self.sunset_offset_minutes = self.args.get("sunset_offset_minutes", -30)        

        # Set the sensor duration threshold (in seconds)
        self.sensor_duration_threshold = 1 * 60  # 1 minute in seconds

        # Set up listeners for motion sensors
        for sensor in self.motion_sensors:
            self.listen_state(self.motion_detected, sensor, new="on")

        # Set up listeners for door sensors
        for door in self.doors:
            self.listen_state(self.door_opened, door, new="on")

        # Set up listeners for light sensors
        for light in self.lights:
            self.listen_state(self.light_turned_on, light, new="on")

        # Set up listeners for vibration sensors
        for sensor in self.vibration_sensors:
            self.listen_state(self.vibration_detected, sensor, new="on")

        # Set up listeners for power usage sensors
        for sensor in self.power_sensors:
            self.listen_state(self.power_usage_changed, sensor)

        # Set up listener for weather changes
        self.listen_state(self.weather_changed, self.weather_entity)

        # Set up listener for timer state changes
        self.listen_state(self.timer_state_changed, self.timer_entity)

        # Run the check_sensors function every 5 minutes
        self.run_every(self.check_sensors, "now", 5 * 60)  # Check sensors every 5 minutes

        # Set up sunrise and sunset listeners with the specified offset values
        self.run_at_sunrise(self.sunrise_callback, offset=self.sunrise_offset_minutes*60)  # Convert minutes to seconds
        self.run_at_sunset(self.sunset_callback, offset=self.sunset_offset_minutes*60)  # Convert minutes to seconds

    # Function called when motion is detected
    def motion_detected(self, entity, attribute, old, new, kwargs):
        self.log(f"Motion detected by {entity}, starting occupancy timer.", log="room_occupancy_manager")
        self.call_service("timer/start", entity_id=self.timer_entity)

    # Function called when a door is opened
    def door_opened(self, entity, attribute, old, new, kwargs):
        if self.room_occupied_on_door_open:
            self.log(f"Door {entity} opened, starting occupancy timer.", log="room_occupancy_manager")
            self.call_service("timer/start", entity_id=self.timer_entity)

    # Function called when a light is turned on
    def light_turned_on(self, entity, attribute, old, new, kwargs):
        timer_state = self.get_state(self.timer_entity)
        if timer_state == "idle":
            self.log(f"Light {entity} turned on, starting occupancy timer.", log="room_occupancy_manager")
            self.call_service("timer/start", entity_id=self.timer_entity)

    # Function called when vibration is detected
    def vibration_detected(self, entity, attribute, old, new, kwargs):
        self.log(f"Vibration detected by {entity}, starting occupancy timer.", log="room_occupancy_manager")
        self.call_service("timer/start", entity_id=self.timer_entity)

    # Function called when power usage changes
    def power_usage_changed(self, entity, attribute, old, new, kwargs):
        if float(new) > self.power_usage_threshold:
            self.log(f"Power usage of {entity} exceeded threshold, starting occupancy timer.", log="room_occupancy_manager")
            self.call_service("timer/start", entity_id=self.timer_entity)

    # Function called when timer state changes
    def timer_state_changed(self, entity, attribute, old, new, kwargs):
        if new == "active" and old != "active":
            weather_state = self.get_state(self.weather_entity)
            if weather_state == "rainy" or weather_state == "pouring" or weather_state == "fog":
                self.log(f"Weather is {weather_state}, turning on lights regardless of time constraints.", log="room_occupancy_manager")
                self.turn_on_lights(ignore_time_constraint=True)
            else:
                self.log(f"Timer became active, turning on lights.", log="room_occupancy_manager")
                self.turn_on_lights()
        elif new == "idle" and old != "idle":
            self.log(f"Timer became idle, turning off lights.", log="room_occupancy_manager")
            self.turn_off_lights()

    # Function to check sensors periodically
    def check_sensors(self, kwargs):
        now = datetime.now(pytz.utc)  # Make the 'now' variable timezone-aware
        for sensor in self.motion_sensors:
            sensor_state = self.get_state(sensor)
            if sensor_state == "on":
                sensor_last_changed = self.get_state(sensor, attribute="last_changed")
                if sensor_last_changed:
                    sensor_last_changed = datetime.strptime(sensor_last_changed, "%Y-%m-%dT%H:%M:%S.%f%z")
                    time_since_last_change = now - sensor_last_changed
                    if time_since_last_change >= timedelta(seconds=self.sensor_duration_threshold):
                        self.call_service("timer/start", entity_id=self.timer_entity)
                        break

        if self.room_occupied_on_door_closed:
            for door in self.doors:
                door_state = self.get_state(door)
                if door_state == "off":
                    self.call_service("timer/start", entity_id=self.timer_entity)
                    break

        #weather_state = self.get_state(self.weather_entity)
        #timer_state = self.get_state(self.timer_entity)
        #if timer_state == "active" and (weather_state == "rainy" or weather_state == "pouring" or weather_state == "fog"):
            #self.turn_on_lights(ignore_time_constraint=True)

    # Function called when weather changes
    def weather_changed(self, entity, attribute, old, new, kwargs):
        timer_state = self.get_state(self.timer_entity)
        if timer_state == "active" and (new == "rainy" or new == "pouring" or new == "fog"):
            self.turn_on_lights(ignore_time_constraint=True)

    # Function called at sunrise
    def sunrise_callback(self, kwargs):
        light_override_state = self.get_state(self.light_override)
        if not self.lights_always_turn_on and light_override_state == "off":
            self.turn_off_lights()

    # Function called at sunset
    def sunset_callback(self, kwargs):
        light_override_state = self.get_state(self.light_override)
        if not self.lights_always_turn_on and light_override_state == "off":
            self.turn_on_lights()

    # Function to calculate sunset time with an offset value
    def is_after_sunset_with_offset(self):
        sunset_time = self.sunset(today=True)
        sunset_with_offset = sunset_time + timedelta(minutes=self.sunset_offset_minutes)
        now = self.datetime()

        return now >= sunset_with_offset or self.sun_down()

    # Function to calculate sunrise time with an offset value
    def is_before_sunrise_with_offset(self):
        sunrise_time = self.sunrise()
        sunrise_with_offset = sunrise_time + timedelta(minutes=self.sunrise_offset_minutes)
        now = self.datetime()

        return now < sunrise_with_offset

    # Function to turn on lights based on conditions
    def turn_on_lights(self, ignore_time_constraint=False):
        light_override_state = self.get_state(self.light_override)
        if light_override_state == "off":
            if ignore_time_constraint:
                self.log("Turning on lights without considering time constraints.", log="room_occupancy_manager")
                for light in self.lights:
                    if self.get_state(light) == "off":
                        self.log(f"Turning on light {light}.")
                        self.turn_on(light)
            else:
                # Use the offset values for sunset and sunrise
                sunset_offset_str = f"sunset {'+ ' if self.sunset_offset_minutes >= 0 else '- '}{abs(self.sunset_offset_minutes) // 60:02d}:{abs(self.sunset_offset_minutes) % 60:02d}:00"
                sunrise_offset_str = f"sunrise {'+ ' if self.sunrise_offset_minutes >= 0 else '- '}{abs(self.sunrise_offset_minutes) // 60:02d}:{abs(self.sunrise_offset_minutes) % 60:02d}:00"
                if self.lights_always_turn_on or self.now_is_between(sunset_offset_str, sunrise_offset_str):
                    self.log("Turning on lights based on time constraints.", log="room_occupancy_manager")
                    for light in self.lights:
                        if self.get_state(light) == "off":
                            self.log(f"Turning on light {light}.", log="room_occupancy_manager")
                            self.turn_on(light)

    # Function to turn off lights based on conditions
    def turn_off_lights(self):
        light_override_state = self.get_state(self.light_override)
        if light_override_state == "off":
            self.log("Turning off lights based on conditions.", log="room_occupancy_manager")
            for light in self.lights:
                if self.get_state(light) == "on":
                    self.log(f"Turning off light {light}.", log="room_occupancy_manager")
                    self.turn_off(light)
