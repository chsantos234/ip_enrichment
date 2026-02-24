from blocklist_file_manager import BlocklistFileManager as blocklist_manager
from open_cti_manager import OpenCTIManager
import pandas as pd
import argparse
import time

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='IP Enrichment Script')
    parser.add_argument('--number_ips', type=int, default=10, help='Number of IPs to process per run')
    parser.add_argument('--wait_time', type=int, default=1, help='Wait time in minutes before retrieving observables from OpenCTI')
    parser.add_argument('--threshold',type=int, default=30, help='Threshold in days for considering an IP outdated')

    args = parser.parse_args()


    df = blocklist_manager.update_local_csv(return_csv=True)
    cti_manager = OpenCTIManager()

    active_ips = blocklist_manager.get_n_active_ips(args.number_ips, threshold=args.threshold)
    for ip in active_ips: print(ip)

    observables = []

    for ip in active_ips:
        observable_input = {
            "type": "IPv4-Addr",
            "value": ip
        }
        labels = ["internal blocklist"]

        observables.append(cti_manager.put_observable(observable_input, labels))

    print(f"waiting {args.wait_time} minutes to allow OpenCTI to process the observables...")
    time.sleep(60*args.wait_time)

    print("retrieving observables from OpenCTI and updating local file...")
    for observable in observables:

        obs = cti_manager.get_observable_by_stix_id(observable['standard_id'])
        blocklist_manager.update_ip_info(obs)

    