"""Airzone diagnostic sensors."""

from datetime import timedelta
import logging

from airzone import airzone_factory

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_HOST, CONF_PORT, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_ID,
    CONF_DEVICE_CLASS,
    CONF_SPEED_PERCENTAGE,
    DEFAULT_DEVICE_ID,
    DEFAULT_DEVICE_CLASS,
    DEFAULT_SPEED_AS_PER,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Airzone diagnostic sensors."""

    config = hass.data[DOMAIN][config_entry.entry_id]

    host = config[CONF_HOST]
    port = config[CONF_PORT]
    machine_id = config.get(CONF_DEVICE_ID, DEFAULT_DEVICE_ID)
    system_class = config.get(CONF_DEVICE_CLASS, DEFAULT_DEVICE_CLASS)
    speed_as_per = config.get(CONF_SPEED_PERCENTAGE, DEFAULT_SPEED_AS_PER)

    machine = await hass.async_add_executor_job(
        lambda: airzone_factory(
            host,
            port,
            machine_id,
            system_class,
            speed_as_per=speed_as_per,
        )
    )

    if system_class != "innobus":
        _LOGGER.warning(
            "Airzone diagnostic sensors are currently only implemented for Innobus"
        )
        return

    entities = []

    # ---------------------------------------------------------
    # REGISTRES MACHINE
    # ---------------------------------------------------------

    for register in range(0, 98):
        entities.append(
            AirzoneMachineRegisterSensor(machine, register)
        )

    # ---------------------------------------------------------
    # REGISTRES ZONES
    # ---------------------------------------------------------

    for zone in machine.zones:
        # Pour commencer : tous les registres de la zone 1 uniquement.
        # On pourra ensuite étendre à toutes les zones.
        if zone._zone_id == 1:
            for register in range(0, 33):
                entities.append(
                    AirzoneZoneRegisterSensor(zone, register)
                )

    async_add_entities(entities)


class AirzoneMachineRegisterSensor(SensorEntity):
    """Airzone machine register."""

    def __init__(self, machine, register):
        self._machine = machine
        self._register = register

        self._attr_name = f"Airzone Machine R{register}"
        self._attr_unique_id = (
            f"{machine.unique_id}_machine_register_{register}"
        )

        self._attr_native_unit_of_measurement = None
        self._attr_icon = "mdi:memory"

    @property
    def native_value(self):
        """Return register value."""
        try:
            state = self._machine._machine_state

            if state is None:
                return None

            if self._register >= len(state):
                return None

            return state[self._register]

        except Exception as err:
            _LOGGER.debug(
                "Erreur lecture registre machine R%s: %s",
                self._register,
                err,
            )
            return None

    def update(self):
        """Update register."""
        try:
            self._machine._retrieve_machine_state()
        except Exception as err:
            _LOGGER.debug(
                "Erreur mise à jour registres machine: %s",
                err,
            )


class AirzoneZoneRegisterSensor(SensorEntity):
    """Airzone zone register."""

    def __init__(self, zone, register):
        self._zone = zone
        self._register = register

        zone_id = zone._zone_id

        self._attr_name = (
            f"Airzone Zone {zone_id} R{register}"
        )

        self._attr_unique_id = (
            f"{zone.unique_id}_register_{register}"
        )

        self._attr_native_unit_of_measurement = None
        self._attr_icon = "mdi:memory"

    @property
    def native_value(self):
        """Return register value."""
        try:
            state = self._zone._zone_state

            if state is None:
                return None

            if self._register >= len(state):
                return None

            return state[self._register]

        except Exception as err:
            _LOGGER.debug(
                "Erreur lecture registre zone R%s: %s",
                self._register,
                err,
            )
            return None

    def update(self):
        """Update zone registers."""
        try:
            self._zone.retrieve_zone_state()
        except Exception as err:
            _LOGGER.debug(
                "Erreur mise à jour registres zone: %s",
                err,
            )
