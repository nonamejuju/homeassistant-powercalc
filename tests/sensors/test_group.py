from homeassistant.components import input_boolean, sensor
from homeassistant.components.utility_meter.sensor import SensorDeviceClass
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_ENTITIES,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_UNIQUE_ID,
    STATE_ON,
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    MockEntity, MockEntityPlatform, MockConfigEntry
)

from custom_components.powercalc.const import (
    ATTR_ENTITIES,
    CONF_CREATE_GROUP,
    CONF_FIXED,
    CONF_GROUP_POWER_ENTITIES,
    CONF_MODE,
    CONF_POWER,
    CONF_POWER_SENSOR_ID,
    CONF_SENSOR_TYPE,
    CONF_SUB_GROUPS,
    DOMAIN,
    CalculationStrategy,
    SensorType,
)


async def test_grouped_power_sensor(hass: HomeAssistant):
    assert await async_setup_component(
        hass, input_boolean.DOMAIN, {"input_boolean": {"test1": None}}
    )
    assert await async_setup_component(
        hass, input_boolean.DOMAIN, {"input_boolean": {"test2": None}}
    )

    await hass.async_block_till_done()

    await async_setup_component(
        hass,
        sensor.DOMAIN,
        {
            sensor.DOMAIN: {
                CONF_PLATFORM: DOMAIN,
                CONF_CREATE_GROUP: "TestGroup",
                CONF_ENTITIES: [
                    {
                        CONF_ENTITY_ID: "input_boolean.test1",
                        CONF_UNIQUE_ID: "4312393932",
                        CONF_MODE: CalculationStrategy.FIXED,
                        CONF_FIXED: {CONF_POWER: 10.5},
                    },
                    {
                        CONF_ENTITY_ID: "input_boolean.test2",
                        CONF_MODE: CalculationStrategy.FIXED,
                        CONF_FIXED: {CONF_POWER: 50},
                    },
                ],
            }
        },
    )

    await hass.async_block_till_done()

    hass.states.async_set("input_boolean.test1", STATE_ON)
    hass.states.async_set("input_boolean.test2", STATE_ON)

    await hass.async_block_till_done()

    power_state = hass.states.get("sensor.testgroup_power")
    assert power_state
    assert power_state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.POWER
    assert power_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == POWER_WATT
    assert power_state.attributes.get(ATTR_ENTITIES) == {
        "sensor.test1_power",
        "sensor.test2_power",
    }
    assert power_state.state == "60.50"

    energy_state = hass.states.get("sensor.testgroup_energy")
    assert energy_state
    assert energy_state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY
    assert energy_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == ENERGY_KILO_WATT_HOUR
    assert energy_state.attributes.get(ATTR_ENTITIES) == {
        "sensor.test1_energy",
        "sensor.test2_energy",
    }

async def test_subgroups_from_config_entry(hass: HomeAssistant):
    config_entry_groupa = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SENSOR_TYPE: SensorType.GROUP,
            CONF_NAME: "GroupA",
            CONF_GROUP_POWER_ENTITIES: [
                "sensor.test1_power"
            ]
        }
    )
    config_entry_groupa.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry_groupa.entry_id)
    await hass.async_block_till_done()

    config_entry_groupb = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SENSOR_TYPE: SensorType.GROUP,
            CONF_NAME: "GroupB",
            CONF_GROUP_POWER_ENTITIES: [
                "sensor.test2_power"
            ],
            CONF_SUB_GROUPS: [
                config_entry_groupa.entry_id,
                "464354354543" # Non existing entry_id, should not break setup
            ]
        }
    )
    config_entry_groupb.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry_groupb.entry_id)
    await hass.async_block_till_done()

    groupa_state = hass.states.get("sensor.groupa_power")
    assert groupa_state
    assert groupa_state.attributes.get(ATTR_ENTITIES) == {
        "sensor.test1_power",
    }
    groupb_state = hass.states.get("sensor.groupb_power")
    assert groupb_state
    assert groupb_state.attributes.get(ATTR_ENTITIES) == {
        "sensor.test1_power",
        "sensor.test2_power",
    }