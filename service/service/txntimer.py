from logging import getLogger
from time import perf_counter

logger = getLogger()


class txntimer:
    def __init__(self, request) -> None:
        self.txnid = request.headers["x-request-id"]

    def __enter__(self):
        self.start = perf_counter()
        logger.info(f"DO txid={self.txnid}")
        return self

    def __exit__(self, type, value, traceback):
        duration = perf_counter() - self.start
        formatted_process_time = f"{duration:.2f}"
        logger.info(f"DONE txid={self.txnid} time={formatted_process_time}")
