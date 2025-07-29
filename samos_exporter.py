#!/usr/bin/env python3
"""
FILE:           samos_exporter.py

DESCRIPTION:    This process export data from InfluxDB in the SAMOS data
                format.

BUGS:
NOTES:
AUTHOR:     Webb Pinner
COMPANY:    Schmidt Ocean Institute
VERSION:    1.1
CREATED:    2022-04-08
REVISION:   2024-08-14

LICENSE INFO:   This code is licensed under GPLv3 license (see LICENSE.txt for
                details). Copyright (C) Schmidt Ocean Institute 2024
"""

import itertools
import json
import logging
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from os.path import dirname, realpath

import yaml

sys.path.append(dirname(realpath(__file__)))
from gmailer_oauth import GMailer  # noqa: E402
from samos_data_builder import SAMOSDataBuilder  # noqa: E402
from settings import (DEST_DIR, EMAIL_FN_PREFIX, FN_PREFIX,  # noqa: E402
                      INLINE_CONFIG, MAILER_CC, MAILER_FROM, MAILER_SUBJECT,
                      MAILER_TEXT, MAILER_TO)


def send_samos_email(dt: datetime, attachment_path: str):
    mailer = GMailer(
        token_file="token.json",
        client_secret_file="client_secret.json",
        sender=MAILER_FROM,
        recipient=MAILER_TO,
    )
    try:
        mailer.send_email(
            subject=f'{MAILER_SUBJECT} - {dt.strftime("%Y-%m-%d")}',
            body=MAILER_TEXT.replace("<date>", dt.strftime("%Y-%m-%d")),
            attachments=[(attachment_path)],
            cc=MAILER_CC
        )

    except Exception:
        logging.exception("Problem emailing SAMOS data")


def save_to_file(dt: datetime, samos_data_fp):
    """
    Save exported SAMOS data to file
    """

    try:
        samos_filename = os.path.join(
            DEST_DIR, f'{FN_PREFIX}_{dt.strftime("%Y-%m-%d")}.csv'
        )

        with open(samos_filename, "w") as fp:
            fp.write(samos_data_fp.read())

    except Exception:
        logging.exception("Problem saving SAMOS data to file")


# -------------------------------------------------------------------------------------
# The main function of the utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="SAMOS Data Exporter")

    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Reduce output verbosity"
    )

    parser.add_argument(
        "-v",
        "--verbosity",
        dest="verbosity",
        default=1,
        action="count",
        help="Increase output verbosity",
    )

    parser.add_argument(
        "-d",
        "--date",
        default=(datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        help="Specify date of data to export (YYYY-mm-dd)",
    )

    parser.add_argument(
        "-e",
        "--email",
        default=False,
        action="store_true",
        help="Send email containing exported data to SAMOS",
    )

    parser.add_argument(
        "-s",
        "--save",
        default=False,
        action="store_true",
        help="Save exported data to file",
    )

    parser.add_argument(
        "-f", "--config_file", help="Used the specifed configuration file"
    )

    parsed_args = parser.parse_args()

    ############################
    # Set up logging before we do any other argument parsing (so that we
    # can log problems with argument parsing).

    LOGGING_FORMAT = "%(asctime)-15s %(levelname)s - %(message)s"
    logging.basicConfig(format=LOGGING_FORMAT)

    LOG_LEVELS = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }

    if parsed_args.quiet:
        logging.getLogger().setLevel(LOG_LEVELS[0])
    else:
        parsed_args.verbosity = min(parsed_args.verbosity, max(LOG_LEVELS))
        logging.getLogger().setLevel(LOG_LEVELS[parsed_args.verbosity])

    samos_data_config = None  # pylint: disable=invalid-name

    if parsed_args.config_file:
        try:
            with open(parsed_args.config_file, "r", encoding="utf-8") as file:
                samos_data_config = yaml.safe_load(file)
        except yaml.parser.ParserError:
            logging.exception("Invalid YAML syntax")
            sys.exit(1)
    else:
        try:
            samos_data_config = yaml.safe_load(INLINE_CONFIG)
        except yaml.parser.ParserError:
            logging.exception("Invalid YAML syntax")
            sys.exit(1)

    logging.debug(json.dumps(samos_data_config, indent=2))

    logging.info("Exporting data starting at: %s", parsed_args.date)

    samos_data_builder = SAMOSDataBuilder(samos_data_config)
    output = samos_data_builder.build_samos_csv(parsed_args.date)

    # If there is no output, exit
    peek = next(output, None)
    if peek is None:
        logging.info("No data found, Quitting")
        sys.exit(0)

    if not (parsed_args.email or parsed_args.save):
        for line in itertools.chain([peek], output):
            print(line)
        sys.exit(0)

    tmp_dir = tempfile.gettempdir()
    samos_fn = f"{EMAIL_FN_PREFIX}_{parsed_args.date.strftime('%Y-%m-%d')}.csv"
    samos_fp = os.path.join(tmp_dir, samos_fn)

    try:
        with open(samos_fp, "w+") as f:
            for line in itertools.chain([peek], output):
                f.write(line)

            f.seek(0)

            # If the data should be emailed to SAMOS
            if parsed_args.email:
                logging.info("Emailing exported data to: %s", MAILER_TO)
                send_samos_email(parsed_args.date, samos_fp)

            if parsed_args.save:
                dest_filename = os.path.join(DEST_DIR, samos_fn)
                shutil.copy(samos_fp, dest_filename)
                logging.info("Saved exported data to: %s", dest_filename)

    finally:
        os.remove(samos_fp)
