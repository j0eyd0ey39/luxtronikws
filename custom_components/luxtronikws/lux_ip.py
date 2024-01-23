import socket
import asyncio

class LuxListener:
	def __init__(self, on_con_lost):
		self._attr_ip = self.getIPAddress()
		self.on_con_lost = on_con_lost
		self._attr_lux_ip = None

	def connection_made(self, transport):
		self.transport = transport

	def connection_lost(self, transport):
		if not self.on_con_lost.cancelled():
			self.on_con_lost.set_result(True)

	def datagram_received(self, data, addr):
		if addr[1] == 4444 and addr[0] != self._attr_ip:
			self._attr_lux_ip = addr[0]
			self.transport.close()

	def getLuxIp(self):
		return self._attr_lux_ip

	def getIPAddress(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		return s.getsockname()[0]

async def getLuxIp():
	# Get a reference to the event loop as we plan to use
	# low-level APIs.
	loop = asyncio.get_running_loop()
	on_con_lost = loop.create_future()
	# One protocol instance will be created to serve all
	# client requests.
	luxListener = LuxListener(on_con_lost)
	transport, protocol = await loop.create_datagram_endpoint(
		lambda: luxListener,
		local_addr=('0.0.0.0', 4444))
	luxIp = "static.luxtronik.ip.here"

	try:
		buffer = bytes([0x32, 0x30, 0x30, 0x30, 0x3b, 0x31, 0x31, 0x31, 0x3b, 0x31, 0x3b, 0x00, 0x00, 0x00, 0x20, 0x20, 0x20, 0x20])
		ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
		ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		ssock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		ssock.sendto(buffer, ("255.255.255.255", 4444))
		await asyncio.wait_for(on_con_lost, timeout=2)
		luxIp = luxListener.getLuxIp()
	except asyncio.exceptions.TimeoutError:
		on_con_lost.cancel()
	finally:
		transport.close()

	return luxIp