import logging


def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        format="[%(asctime)s] %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
        level=logging.DEBUG if verbose else logging.INFO,
    )
