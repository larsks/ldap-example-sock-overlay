import asyncio
import itertools
import logging
import os
import sys

SOCKET_PATH = os.getenv("SLAPO_SOCKET_PATH", "slapo_socket")
LOG = logging.getLogger(__name__)


class SocketLogger:
    def __init__(self, socket_path):
        self.socket_path = socket_path
        self.counter = itertools.count()

    async def start(self):
        try:
            os.unlink(self.socket_path)
        except OSError:
            if os.path.exists(self.socket_path):
                raise

        server = await asyncio.start_unix_server(
            self.handle_connection,
            path=self.socket_path,
        )
        os.chmod(self.socket_path, 0o666)
        await server.serve_forever()

    async def handle_connection(self, reader, writer):
        mark = next(self.counter)
        LOG.info(f"start connection handler {mark}")
        while True:
            line = await reader.readline()
            if not line:
                LOG.info("client disconnected")
                break
            if line == b"\n":
                writer.write(b"RESULT\n")
                break

            print(mark, ":", line.decode().strip())
            sys.stdout.flush()

        try:
            writer.close()
            await writer.wait_closed()
        except BrokenPipeError:
            pass


async def main():
    app = SocketLogger(SOCKET_PATH)
    print("starting")
    await app.start()
    print("done")


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    asyncio.run(main())
