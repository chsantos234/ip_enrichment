import hashlib
import requests
#import ipaddress
import pandas as pd
from pathlib import Path
from dotenv import dotenv_values

config = dotenv_values(".env")

RAW_FILE = Path(config["SERPRO_RAW_FILE_PATH"])
FORMATTED_FILE = Path(config["SERPRO_FORMATTED_FILE_PATH"])
PROCESSED_IP_FILE = Path(config["PROCESSED_IP_FILE_PATH"])

class BlocklistFileManager:
    @staticmethod
    def sha256_from_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def format_text(text: str) -> str:
        lines = []
        for line in text.splitlines():
            ip = line.strip()
            if ip:
                lines.append(f"{ip}: ")
        return "\n".join(lines) + "\n"

    @staticmethod
    def update_local_file() -> bool:
        #_ = sys.stdin.read()
        response = requests.get(config["SERPRO_BLOCKLIST_URL"], timeout=30)
        response.raise_for_status()
        remote_text = response.text
        remote_hash = BlocklistFileManager.sha256_from_text(remote_text)
        local_hash = None

        if RAW_FILE.exists():
            local_text = RAW_FILE.read_text(encoding="utf-8")
            local_hash = BlocklistFileManager.sha256_from_text(local_text)
        else: print("creating new local files...")

        if remote_hash != local_hash:
            print('remote file has changed, updating local file...')
            RAW_FILE.write_text(remote_text, encoding="utf-8")
            FORMATTED_FILE.write_text(BlocklistFileManager.format_text(remote_text), encoding="utf-8")
            return True
        
        print("local file is up to date")
        return False
    
    @staticmethod
    def update_local_csv(return_csv : bool=False) -> pd.DataFrame | None:
        updated = BlocklistFileManager.update_local_file()

        if PROCESSED_IP_FILE.exists():
            df = pd.read_csv(PROCESSED_IP_FILE)

            if updated:
                print("updating existing csv file...")
                
                new_ips = pd.read_csv(RAW_FILE, header=None, names=["ip"])
                new_ips["active"] = True
                new_ips["upload_date"] = None
                
                df = pd.concat([df, new_ips], ignore_index=True).drop_duplicates(subset=["ip"]).reset_index(drop=True)

                # Deactivate missing IPs
                current_active_ips = set(df[df["active"] == True]["ip"])
                new_ips_set = set(new_ips["ip"])
                ips_to_deactivate = current_active_ips - new_ips_set
                
                df.loc[df["ip"].isin(ips_to_deactivate), "active"] = False

                # Reactivate reappearing IPs
                ips_to_reactivate = new_ips_set & set(df[df["active"] == False]["ip"])

                if ips_to_reactivate:
                    df.loc[df["ip"].isin(ips_to_reactivate), "active"] = True

                df.to_csv(PROCESSED_IP_FILE, index=False)
            print("csv file is up to date")
            return
        
        print("creating a new csv file...")
        df = (pd.read_csv(RAW_FILE, header=None, skip_blank_lines=True, names=["ip"]).drop_duplicates().reset_index(drop=True))
        df["active"] = True
        df['score'] = -1
        df['tags'] = None
        df["upload_date"] = None

        df.to_csv(PROCESSED_IP_FILE, index=False)
        if return_csv:return df
