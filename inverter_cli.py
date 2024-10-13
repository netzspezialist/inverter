import argparse
import logging

from binascii import unhexlify
from inverter_connection import InverterConnection

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Description of your CLI tool')

    # Add arguments
    parser.add_argument('-c', '--command', type=str, help='Command to send to the inverter')

    # Parse arguments
    args = parser.parse_args()

    # Access the values of the arguments
    cmd = args.command

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(logging.Formatter('%(levelname)8s | %(message)s'))
    logger.addHandler(stdout_handler)

    inverter = InverterConnection(logger)

    inverter.execute(cmd)

    inverter.close()
        
if __name__ == '__main__':
    main()