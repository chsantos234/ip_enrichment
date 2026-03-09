import time
import logging
import argparse
from datetime import datetime, timezone
from ip_enrichment.opencti.manager import OpenCTIManager
from ip_enrichment.blocklist.manager import BlocklistFileManager as blocklist_manager

from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)


def wait_for_enrichment(cti_manager, stix_id, ip_value, timeout=60) -> dict | None:
    start = time.time()
    index = 1
    while time.time() - start < timeout:
        response = cti_manager.get_observable_by_stix_id(stix_id)
        if response['externalReferences'] != []:
            return response
        logger.info(f"Waiting for enrichment of {ip_value} - {stix_id} (attempt {index})")
        time.sleep(10)
        index += 1
    return None

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler("enrichment.log"),
            logging.StreamHandler()
        ]
    )

    parser = argparse.ArgumentParser(description='IP Enrichment CLI')
    subparsers = parser.add_subparsers(dest='command', required=True)

    enrich_parser = subparsers.add_parser("enrich", help="Send new IPs for enrichment and update local CSV with results")
    enrich_parser.add_argument('--number_ips', type=int, default=10, help='Max number of IPs to process per run')
    enrich_parser.add_argument('--threshold',type=int, default=30, help='Threshold in days for considering an IP outdated')

    #refresh_parser = subparsers.add_parser("refresh", help="Refresh all csv data for existing active enriched IPs ")
    subparsers.add_parser("refresh", help="Refresh all csv data for existing active enriched IPs ")


    args = parser.parse_args()

    border = "=" * 70
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    params_line = ""
    if args.command == "enrich":
        params_line = f"  number_ips : {args.number_ips} ips\n  threshold  : {args.threshold} days\n"

    header = (
        f"\n\n{border}\n"
        f"  SCRIPT STARTED — {args.command.upper()}\n"
        f"  Timestamp  : {timestamp}\n"
        f"{params_line}"
        f"{border}\n\n"
    )

    logger.info(header)

    if args.command == "enrich":
        run_enrichment(args)

    elif args.command == "refresh":
        refresh_existing()


def run_enrichment(args):
    blocklist_manager.update_local_csv(return_csv=False)
    cti_manager = OpenCTIManager()

    active_ips = blocklist_manager.get_n_active_ips(args.number_ips, threshold=args.threshold)
    logger.info(f'{active_ips}')

    observables = []
    observable_ips = []

    for ip in active_ips:
        try:
            observable = cti_manager.put_observable(
                {"type": "IPv4-Addr","value": ip},
                ["internal blocklist"]
            )

            if not observable:
                logger.warning(f"Failed to create/update observable for {ip}")
                continue

            observables.append(observable)
            observable_ips.append(ip)
        except Exception as e:
            logger.warning(f"Error creating/updating observable for {ip}: {e}")

    for i, observable in enumerate(observables):
        response =  wait_for_enrichment(cti_manager, observable['standard_id'], observable_ips[i])

        if not response:
            logger.warning(f"Timeout waiting for enrichment of {observable['standard_id']}")
            continue

        blocklist_manager.update_ip_info(response)


def refresh_existing():
    df = blocklist_manager.update_local_csv(return_csv=True)
    cti_manager = OpenCTIManager()
    
    if df is None:
        logger.warning("Failed to retrieve CSV data")
        return None
    
    ips_to_refresh = df[df["active"] & df["upload_date"].notna()]
    ip_list = ips_to_refresh["ip"].to_numpy()

    logger.info(f"Refreshing {len(ip_list)} active enriched IPs")

    results = []
    lock = threading.Lock()

    def fetch(ip):
        response = cti_manager.get_ipv4_observable_by_value(ip)
        if not response:
            logger.warning(f"Failed to retrieve observable for {ip}")
            return
        with lock:
            results.append(response)


    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch,ip): ip for ip in ip_list}

        for future in as_completed(futures):
            if e := future.exception():
                logger.error(f"Error processing {futures[future]}: {e}")


    for response in results:
        blocklist_manager.update_ip_info(response)

    #for i, row in ips_to_refresh.iterrows():
    #    response = cti_manager.get_ipv4_observable_by_value(row["ip"])
    #
    #    if not response:
    #        logger.warning(f"Failed to retrieve observable for {row['ip']}")
    #        continue
    #
    #    blocklist_manager.update_ip_info(response)

if __name__ == "__main__":
    main()
    


# does api on opencti need to be resent for enrichment or does it automatically update periodically when enrichment is done on opencti side?