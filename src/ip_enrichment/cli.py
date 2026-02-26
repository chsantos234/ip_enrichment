from ip_enrichment.blocklist.manager import BlocklistFileManager as blocklist_manager
from ip_enrichment.opencti.manager import OpenCTIManager
import argparse
import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

#TODO: add retry logic for API calls
def wait_for_enrichment(cti_manager, stix_id, timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        obs = cti_manager.get_observable_by_stix_id(stix_id)
        if obs.get("x_opencti_score") is not None:
            return obs
        time.sleep(10)
    return None


def main():
    logging.basicConfig(filename='enrichment.log', level=logging.INFO)

    parser = argparse.ArgumentParser(description='IP Enrichment Script')
    parser.add_argument('--number_ips', type=int, default=10, help='Max number of IPs to process per run')
    parser.add_argument('--wait_time', type=int, default=1, help='Wait time in minutes before retrieving data from APIs') # TODO: remove later and replace with dynamic wait based on enrichment status
    parser.add_argument('--threshold',type=int, default=30, help='Threshold in days for considering an IP outdated')

    args = parser.parse_args()

    logger.info(f"{datetime.now(timezone.utc)} - Script started with parameters: number_ips={args.number_ips}, wait_time={args.wait_time}, threshold={args.threshold}")

    df = blocklist_manager.update_local_csv(return_csv=True)
    cti_manager = OpenCTIManager()

    active_ips = blocklist_manager.get_n_active_ips(args.number_ips, threshold=args.threshold)
    logger.info(f'{active_ips}')

    observables = []

    for ip in active_ips:
        observable_input = {
            "type": "IPv4-Addr",
            "value": ip
        }
        labels = ["internal blocklist"]

        observables.append(cti_manager.put_observable(observable_input, labels))

    time.sleep(60*args.wait_time)

    for observable in observables:

        obs = cti_manager.get_observable_by_stix_id(observable['standard_id'])
        if obs is not None: blocklist_manager.update_ip_info(obs)

if __name__ == "__main__":
    main()
    