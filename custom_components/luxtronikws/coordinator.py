from .config_flow import getWebsocket
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from homeassistant.core import HomeAssistant
from datetime import timedelta
import async_timeout
import logging
import xml.etree.ElementTree as ET

_LOGGER = logging.getLogger(__name__)


class LuxtronikCoordinator(DataUpdateCoordinator):
    """Luxtronik custom coordinator."""

    def __init__(self, hass: HomeAssistant, server, password, update_interval) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="LuxtronikCoordinator",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=update_interval),
        )
        self._attr_server = server
        self._attr_password = password

    async def _ainit(self) -> None:
        ws, root, _, _ = await getWebsocket(self._attr_server, self._attr_password)
        self._attr_ws = ws
        self._attr_root = root

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        # handled by the data update coordinator.
        async with async_timeout.timeout(10):
            await self._ainit()
            # send ws queries for item ids
            listedItems = list(list(self._attr_root)[0])

            await self._attr_ws.send("GET;"+listedItems[1].attrib["id"])
            result = await self._attr_ws.recv()
            tempsroot = ET.fromstring(result)

            await self._attr_ws.send("GET;"+listedItems[2].attrib["id"])
            result = await self._attr_ws.recv()
            inputsroot = ET.fromstring(result)

            await self._attr_ws.send("GET;"+listedItems[3].attrib["id"])
            result = await self._attr_ws.recv()
            outputsroot = ET.fromstring(result)

            await self._attr_ws.send("GET;"+listedItems[4].attrib["id"])
            result = await self._attr_ws.recv()
            timesroot = ET.fromstring(result)

            await self._attr_ws.send("GET;"+listedItems[8].attrib["id"])
            result = await self._attr_ws.recv()
            deviceinforoot = ET.fromstring(result)

            await self._attr_ws.send("GET;"+listedItems[9].attrib["id"])
            result = await self._attr_ws.recv()
            energyroot = ET.fromstring(result)

            await(self._attr_ws.close())

            return {
                "temperatures": tempsroot,
                "inputs": inputsroot,
                "outputs": outputsroot,
                "deviceinfo": deviceinforoot,
                "times": timesroot,
                "energyOutputs": list(energyroot)[0],
                "energyInputs": list(energyroot)[1],
            }
            # globber results to dict
            # return result data

    def appendXMLListToDictList(self, typeValue, swValue, xmlList, dict, groupName):
        i = 0
        for item in xmlList:
            sublist = list(item)
            if len(sublist) == 2:
                dict.append({"type": typeValue, "sw": swValue, "name": sublist[0].text, "index": i, "group": groupName })

            i = i + 1

    def listEntities(self):
        root = self.data["deviceinfo"]
        listed = list(root)
        typeValue = list(listed[0])[1].text
        swValue = list(listed[1])[1].text
        stateName = list(listed[7])[0].text
        capacityName = list(listed[8])[0].text

        powerDicts = [{"type": typeValue, "sw": swValue, "name": capacityName, "index": 8, "group": "deviceinfo" }]

        listed = list(self.data["temperatures"])
        tempDicts = []
        self.appendXMLListToDictList(typeValue, swValue, listed, tempDicts, "temperatures")

        listed = list(self.data["inputs"])
        pressureDicts = []
        pressureDicts.append({"type": typeValue, "sw": swValue, "name": list(listed[4])[0].text, "index": 4, "group": "inputs" })
        pressureDicts.append({"type": typeValue, "sw": swValue, "name": list(listed[5])[0].text, "index": 5, "group": "inputs" })

        listed = list(self.data["outputs"])
        frequencyDicts = [{"type": typeValue, "sw": swValue, "name": list(listed[10])[0].text, "index": 10, "group": "outputs" }]
        percentageDicts = []
        percentageDicts.append({"type": typeValue, "sw": swValue, "name": list(listed[12])[0].text, "index": 12, "group": "outputs" })
        percentageDicts.append({"type": typeValue, "sw": swValue, "name": list(listed[13])[0].text, "index": 13, "group": "outputs" })

        listed = list(self.data["energyOutputs"])
        energyDicts = []
        energyDicts.append({"type": typeValue, "sw": swValue, "name": list(listed[1])[0].text+" (output)", "index": 1, "group": "energyOutputs" })
        energyDicts.append({"type": typeValue, "sw": swValue, "name": list(listed[2])[0].text+" (output)", "index": 2, "group": "energyOutputs" })
        energyDicts.append({"type": typeValue, "sw": swValue, "name": list(listed[3])[0].text+" (output)", "index": 3, "group": "energyOutputs" })

        listed = list(self.data["energyInputs"])
        energyDicts.append({"type": typeValue, "sw": swValue, "name": list(listed[1])[0].text+" (input)", "index": 1, "group": "energyInputs" })
        energyDicts.append({"type": typeValue, "sw": swValue, "name": list(listed[2])[0].text+" (input)", "index": 2, "group": "energyInputs" })
        energyDicts.append({"type": typeValue, "sw": swValue, "name": list(listed[3])[0].text+" (input)", "index": 3, "group": "energyInputs" })

        listed = list(self.data["times"])
        timeDicts = []
        self.appendXMLListToDictList(typeValue, swValue, listed, timeDicts, "times")

        return tempDicts, pressureDicts, frequencyDicts, percentageDicts, powerDicts, energyDicts, timeDicts
