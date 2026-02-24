from blocklist_file_manager import BlocklistFileManager as blocklist_manager
from open_cti_manager import OpenCTIManager
import pandas as pd
import time

if __name__ == "__main__":
    df = blocklist_manager.update_local_csv(return_csv=True)
    cti_manager = OpenCTIManager()

    n_ips = 10 # number of IPs to process per run
    min_wait = 1 # wait time in minutes before retrieving observables from OpenCTI

    active_ips = blocklist_manager.get_n_active_ips(n_ips)
    for ip in active_ips: print(ip)

    observables = []

    for ip in active_ips:
        observable_input = {
            "type": "IPv4-Addr",
            "value": ip
        }
        labels = ["internal blocklist"]

        observables.append(cti_manager.put_observable(observable_input, labels))

    print(f"waiting {min_wait} minutes to allow OpenCTI to process the observables...")
    time.sleep(60*min_wait)

    print("retrieving observables from OpenCTI and updating local file...")
    for observable in observables:

        obs = cti_manager.get_observable_by_stix_id(observable['standard_id'])
        blocklist_manager.update_ip_info(obs)

    