from ip_enrichment.blocklist.manager import BlocklistFileManager as blocklist_manager
from ip_enrichment.opencti.manager import OpenCTIManager
import argparse
import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def wait_for_enrichment(cti_manager, stix_id, timeout=61):
    start = time.time()
    index = 1
    while time.time() - start < timeout:
        response = cti_manager.get_observable_by_stix_id(stix_id)
        if response['externalReferences'] != []:
            return response
        logger.info(f"Waiting for enrichment of {stix_id} (attempt {index})")
        time.sleep(10)
        index += 1
    return None


def main():
    logging.basicConfig(filename='enrichment.log', level=logging.INFO)

    parser = argparse.ArgumentParser(description='IP Enrichment Script')
    parser.add_argument('--number_ips', type=int, default=10, help='Max number of IPs to process per run')
    #parser.add_argument('--wait_time', type=int, default=1, help='Wait time in minutes before retrieving data from APIs')
    parser.add_argument('--threshold',type=int, default=30, help='Threshold in days for considering an IP outdated')

    args = parser.parse_args()

    logger.info(f"{datetime.now(timezone.utc)} - Script started with parameters: number_ips={args.number_ips}, threshold={args.threshold}")

    df = blocklist_manager.update_local_csv(return_csv=True)
    cti_manager = OpenCTIManager()

    active_ips = blocklist_manager.get_n_active_ips(args.number_ips, threshold=args.threshold)
    logger.info(f'{active_ips}')

    observables = []

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

        except Exception as e:
            logger.warning(f"Error creating/updating observable for {ip}: {e}")

    for observable in observables:
        response =  wait_for_enrichment(cti_manager, observable['standard_id'])

        if not response:
            logger.warning(f"Timeout waiting for enrichment of {observable['standard_id']}")
            continue

        blocklist_manager.update_ip_info(response)

if __name__ == "__main__":
    main()
    