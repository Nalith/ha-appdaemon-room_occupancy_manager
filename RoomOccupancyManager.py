import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, timedelta
import pytz

# RoomOccupancyManager class that inherits from hass.Hass
class RoomOccupancyManager(hass.Hass):

    def initialize(self):
        self.status_sensor = f"sensor.{self.name.lower().replace(' ', '_')}_app_status"
        self.set_state(self.status_sensor, state="running")

        # Get required parameters from configuration
        self.motion_sensors = self.args["motion_sensors"]
        self.timer_entity = self.args["timer_entity"]
        self.lights = self.args["lights"]
        self.doors = self.args["doors"]
        self.room_occupied_on_door_open = self.args["room_occupied_on_door_open"]
        self.room_occupied_on_door_closed = self.args["room_occupied_on_door_closed"]
        self.sun_elevation_threshold = self.args["sun_elevation_threshold"]
        self.lights_always_turn_on = self.args["lights_always_turn_on"]
        self.light_override = self.args["light_override"]
        self.vibration_sensors = self.args["vibration_sensors"]
        self.power_sensors = self.args["power_sensors"]
        self.power_usage_threshold = self.args["power_usage_threshold"]
        self.weather_entity = self.args["weather_entity"]

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

        # Set up listener for sun elevation changes
        self.listen_state(self.sun_elevation_changed, "sun.sun", attribute="elevation")

    # Function to get home location (latitude and longitude)
    def get_home_location(self):
        latitude = float(self.get_state("zone.home", attribute="latitude"))
        longitude = float(self.get_state("zone.home", attribute="longitude"))
        return latitude, longitude

    # Function to determine the current season based on location and date
    def get_current_season(self):
        latitude, _ = self.get_home_location()
        month = self.datetime().month
        if latitude >= 0:  # Northern Hemisphere
            if 3 <= month < 6:
                return "spring"
            elif 6 <= month < 9:
                return "summer"
            elif 9 <= month < 12:
                return "autumn"
            else:
                return "winter"
        else:  # Southern Hemisphere
            if 3 <= month < 6:
                return "autumn"
            elif 6 <= month < 9:
                return "winter"
            elif 9 <= month < 12:
                return "spring"
            else:
                return "summer"

    # Function called when motion is detected
    def motion_detected(self, entity, attribute, old, new, kwargs):
        self.call_service("timer/start", entity_id=self.timer_entity)

    # Function called when a door is opened
    def door_opened(self, entity, attribute, old, new, kwargs):
        if self.room_occupied_on_door_open:
            self.call_service("timer/start", entity_id=self.timer_entity)

    # Function called when a light is turned on
    def light_turned_on(self, entity, attribute, old, new, kwargs):
        timer_state = self.get_state(self.timer_entity)
        if timer_state == "idle":
            self.call_service("timer/start", entity_id=self.timer_entity)

    # Function called when vibration is detected
    def vibration_detected(self, entity, attribute, old, new, kwargs):
        self.call_service("timer/start", entity_id=self.timer_entity)

    # Function called when power usage changes
    def power_usage_changed(self, entity, attribute, old, new, kwargs):
        if float(new) > self.power_usage_threshold:
            self.call_service("timer/start", entity_id=self.timer_entity)

    # Function called when timer state changes
    def timer_state_changed(self, entity, attribute, old, new, kwargs):
        if new == "active" and old != "active":
            self.turn_on_lights()
        elif new == "idle" and old != "idle":
            self.log("Room is unoccupied")
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

    # Function called when weather changes
    def weather_changed(self, entity, attribute, old, new, kwargs):
        timer_state = self.get_state(self.timer_entity)
        if timer_state == "active" and (new == "rainy" or new == "pouring"):
            self.turn_on_lights(ignore_sun_elevation=True)

    # Function called when sun elevation changes
    def sun_elevation_changed(self, entity, attribute, old, new, kwargs):
        sun_elevation = float(new)
        light_override_state = self.get_state(self.light_override)

        current_sun_elevation_threshold = self.get_sun_elevation_threshold_with_season_offset()

        if sun_elevation < current_sun_elevation_threshold and not self.lights_always_turn_on and light_override_state == "off":
            self.turn_on_lights()
        elif sun_elevation > current_sun_elevation_threshold and not self.lights_always_turn_on and light_override_state == "off":
            self.turn_off_lights()

    # Function to get the sun elevation threshold with season offset
    def get_sun_elevation_threshold_with_season_offset(self):
        season = self.get_current_season()
        if season == "autumn" or season == "spring":
            return self.sun_elevation_threshold + 1
        elif season == "winter":
            return self.sun_elevation_threshold + 2
        else:
            return self.sun_elevation_threshold

    # Function to turn on lights based on conditions
    def turn_on_lights(self, ignore_sun_elevation=False):
        light_override_state = self.get_state(self.light_override)
        if light_override_state == "off":
            if ignore_sun_elevation:
                for light in self.lights:
                    if self.get_state(light) == "off":
                        self.turn_on(light)
            else:
                sun_elevation = float(self.get_state("sun.sun", attribute="elevation"))
                if self.lights_always_turn_on or sun_elevation < self.sun_elevation_threshold:
                    for light in self.lights:
                        if self.get_state(light) == "off":
                            self.turn_on(light)

    # Function to turn off lights based on conditions
    def turn_off_lights(self):
        light_override_state = self.get_state(self.light_override)
        if light_override_state == "off":
            for light in self.lights:
                if self.get_state(light) == "on":
                    self.turn_off(light)
