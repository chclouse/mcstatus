from mcstatus.pinger import ServerPinger
from mcstatus.protocol.connection import TCPSocketConnection, UDPSocketConnection
from mcstatus.querier import ServerQuerier
from mcstatus.scripts.address_tools import parse_address
import dns.resolver


class MinecraftServer:
    def __init__(self, host, port=25565):
        self.host = host
        self.port = port

    @staticmethod
    def lookup(address):
        host, port = parse_address(address)
        if port is None:
            port = 25565
            try:
                answers = dns.resolver.query("_minecraft._tcp." + host, "SRV")
                if len(answers):
                    answer = answers[0]
                    host = str(answer.target).rstrip(".")
                    port = int(answer.port)
            except Exception:
                pass

        return MinecraftServer(host, port)

    async def ping(self, retries=3, **kwargs):
        exception = None
        for attempt in range(retries):
            try:
                connection = await TCPSocketConnection.connect((self.host, self.port))
                pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)
                await pinger.handshake()
                return await pinger.test_ping()
            except Exception as e:
                exception = e
        else:
            raise exception

    async def status(self, retries=3, **kwargs):
        exception = None
        for attempt in range(retries):
            try:
                connection = await TCPSocketConnection.connect((self.host, self.port))
                pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)
                await pinger.handshake()
                result = await pinger.read_status()
                result.latency = await pinger.test_ping()
                return result
            except Exception as e:
                exception = e
        else:
            raise exception

    async def query(self, retries=3):
        exception = None
        host = self.host
        try:
            answers = dns.resolver.query(host, "A")
            if len(answers):
                answer = answers[0]
                host = str(answer).rstrip(".")
        except Exception as e:
            pass
        for attempt in range(retries):
            try:
                connection = await UDPSocketConnection.connect((host, self.port))
                querier = ServerQuerier(connection)
                await querier.handshake()
                return await querier.read_query()
            except Exception as e:
                exception = e
        else:
            raise exception
