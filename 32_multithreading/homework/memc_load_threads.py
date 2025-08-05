#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import concurrent.futures as cf
import glob
import gzip
import logging
import collections
import os
import sys
from optparse import OptionParser
from typing import Optional

import appsinstalled_pb2  # сгенерировано protoc ≥ 3.21
import memcache           # pip install python-memcached

NORMAL_ERR_RATE = 0.01
AppsInstalled = collections.namedtuple(
    "AppsInstalled",
    ["dev_type", "dev_id", "lat", "lon", "apps"]
)


# ---------- util helpers -------------------------------------------------- #
def dot_rename(path: str) -> None:
    """Atomically префиксирует файл точкой, помечая «обработан»."""
    head, fn = os.path.split(path)
    os.rename(path, os.path.join(head, f".{fn}"))


def insert_appsinstalled(
    memc_addr: str,
    appsinstalled: AppsInstalled,
    dry_run: bool = False,
) -> bool:
    """Serialize & write protobuf UserApps → memcached."""
    ua = appsinstalled_pb2.UserApps()
    ua.lat = appsinstalled.lat
    ua.lon = appsinstalled.lon
    ua.apps.extend(appsinstalled.apps)

    key = f"{appsinstalled.dev_type}:{appsinstalled.dev_id}"
    packed = ua.SerializeToString()

    try:
        if dry_run:
            logging.debug("%s - %s -> %s",
                          memc_addr, key, str(ua).replace("\n", " "))
        else:
            memc = memcache.Client([memc_addr])
            memc.set(key, packed)
    except Exception as e:
        logging.exception("Cannot write to memc %s: %s", memc_addr, e)
        return False
    return True


def parse_appsinstalled(line: str) -> Optional[AppsInstalled]:
    """Parse one TSV line → AppsInstalled | None on error."""
    parts = line.strip().split("\t")
    if len(parts) < 5:
        return None

    dev_type, dev_id, lat, lon, raw_apps = parts
    if not dev_type or not dev_id:
        return None

    try:
        apps = [int(a) for a in raw_apps.split(",") if a.isdigit()]
    except ValueError:
        logging.info("Not all user apps are digits: `%s`", line)
        return None

    try:
        lat_f, lon_f = float(lat), float(lon)
    except ValueError:
        logging.info("Invalid geo coords: `%s`", line)
        return None

    return AppsInstalled(dev_type, dev_id, lat_f, lon_f, apps)


# ---------- multithreaded processing ------------------------------------- #
def handle_line(
    line: str,
    device_memc: dict,
    dry_run: bool,
) -> bool:
    """Worker-функция: parse → memcached. Возвращает True|False."""
    if not line:
        return False
    ai = parse_appsinstalled(line)
    if not ai:
        return False

    memc_addr = device_memc.get(ai.dev_type)
    if not memc_addr:
        logging.error("Unknown device type: %s", ai.dev_type)
        return False

    return insert_appsinstalled(memc_addr, ai, dry_run)


def process_file(
    filename: str,
    device_memc: dict,
    dry_run: bool,
    workers: int,
) -> None:
    """Process one .tsv.gz file with multithreaded line handling."""
    processed = errors = 0
    logging.info("Processing %s", filename)

    with gzip.open(filename, mode="rt", encoding="utf-8") as fd, \
            cf.ThreadPoolExecutor(max_workers=workers) as executor:

        futures = [
            executor.submit(handle_line, line.strip(), device_memc, dry_run)
            for line in fd
            if line.strip()
        ]

        for fut in cf.as_completed(futures):
            try:
                ok = fut.result()
            except Exception as e:  # worker raised
                logging.exception("Unhandled exception in worker: %s", e)
                ok = False

            if ok:
                processed += 1
            else:
                errors += 1

    if not processed:
        dot_rename(filename)
        return

    err_rate = errors / processed
    if err_rate < NORMAL_ERR_RATE:
        logging.info("Acceptable error rate (%.3f). Successful load", err_rate)
    else:
        logging.error("High error rate (%.3f > %.2f). Failed load",
                      err_rate, NORMAL_ERR_RATE)

    dot_rename(filename)


# ---------- main entry ---------------------------------------------------- #
def main(options) -> None:
    device_memc = {
        "idfa": options.idfa,
        "gaid": options.gaid,
        "adid": options.adid,
        "dvid": options.dvid,
    }

    # glob.glob уже возвращает в «случайном» порядке → сортируем по имени
    for fn in sorted(glob.iglob(options.pattern)):
        process_file(fn, device_memc, options.dry, options.workers)


def prototest() -> None:
    """Мини-тест корректности сериализации / десериализации protobuf."""
    sample = (
        "idfa\t1rfw\t55.55\t42.42\t1,2,3\n"
        "gaid\t7rfw\t55.55\t42.42\t4,5"
    )
    for line in sample.splitlines():
        dev_type, dev_id, lat, lon, raw_apps = line.split("\t")
        ua = appsinstalled_pb2.UserApps()
        ua.lat = float(lat)
        ua.lon = float(lon)
        ua.apps.extend(map(int, raw_apps.split(",")))

        packed = ua.SerializeToString()
        unpacked = appsinstalled_pb2.UserApps()
        unpacked.ParseFromString(packed)
        assert ua == unpacked, "Protobuf round-trip failed"


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-t", "--test", action="store_true", default=False,
                  help="Run protobuf self-test and exit")
    op.add_option("-l", "--log", action="store",
                  help="Path to log-file (stdout if omitted)")
    op.add_option("--dry", action="store_true", default=False,
                  help="Dry-run: log writes instead of sending to memcached")
    op.add_option("--pattern", action="store",
                  default="/data/appsinstalled/*.tsv.gz",
                  help="Glob pattern with TSV dumps")
    op.add_option("--idfa", action="store", default="127.0.0.1:33013")
    op.add_option("--gaid", action="store", default="127.0.0.1:33014")
    op.add_option("--adid", action="store", default="127.0.0.1:33015")
    op.add_option("--dvid", action="store", default="127.0.0.1:33016")
    op.add_option("--workers", action="store", type="int", default=8,
                  help="ThreadPool size (default: 8)")
    opts, _ = op.parse_args()

    logging.basicConfig(
        filename=opts.log,
        level=logging.INFO if not opts.dry else logging.DEBUG,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )

    if opts.test:
        prototest()
        sys.exit(0)

    logging.info("Memc loader started with options: %s", opts)
    try:
        main(opts)
    except Exception as e:  # noqa: BLE001
        logging.exception("Unexpected error: %s", e)
        sys.exit(1)
