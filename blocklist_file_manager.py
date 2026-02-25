import hashlib
import requests
import pandas as pd
from pathlib import Path
from dotenv import dotenv_values
from datetime import datetime, timezone

config = dotenv_values(".env")

RAW_FILE = Path(config["RAW_FILE_PATH"])
FORMATTED_FILE = Path(config["FORMATTED_FILE_PATH"])
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
        response = requests.get(config["BLOCKLIST_URL"], timeout=30)
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
    def get_n_active_ips(n: int,threshold: int) -> list[str]:
        """
        Return the first `n` IPs where:
        - active is True,
        - upload date is within the last `threshold` days.
        """
        if not PROCESSED_IP_FILE.exists():
            raise FileNotFoundError("Processed IP file not found.")

        df = BlocklistFileManager.load_processed_df()

        now = datetime.now(timezone.utc)
        df["upload_date"] = pd.to_datetime(df["upload_date"], errors="coerce", utc=True)
        outdated = (df["upload_date"].isna() | ((now - df["upload_date"]) > pd.Timedelta(days=threshold)))

        active_ips = df[(df["active"] == True) & (outdated)]["ip"].head(n)

        return active_ips.tolist()
    

    @staticmethod
    def update_ip_info(observable: dict) -> None:
        ip = observable["observable_value"]

        tags = [label["value"] for label in observable["objectLabel"]]

        df = BlocklistFileManager.load_processed_df()
        df.loc[df["ip"] == ip, "upload_date"] = str(pd.to_datetime(observable["updated_at"],utc=True,unit="s"))
        df.loc[df["ip"] == ip, "stix_id"] = observable["standard_id"]
        df.loc[df["ip"] == ip, "score"] = observable['x_opencti_score']
        df.loc[df["ip"] == ip, "tags"] = ",".join(tags) if tags else None

        df.to_csv(PROCESSED_IP_FILE, index=False)

    @staticmethod
    def load_processed_df() -> pd.DataFrame:
        df = pd.read_csv(PROCESSED_IP_FILE)

        df["active"] = df["active"].astype(bool)
        df["score"] = pd.to_numeric(df["score"], errors="coerce")
        df["upload_date"] = df["upload_date"].astype(str)
        df['stix_id'] = df['stix_id'].astype(str)
        df["tags"] = df["tags"].astype("string").fillna("")

        return df


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

                # Reactivate reappearing IPs - remove prevous info? is necessary to update before threshold?? 
                ips_to_reactivate = new_ips_set & set(df[df["active"] == False]["ip"])

                if ips_to_reactivate:
                    df.loc[df["ip"].isin(ips_to_reactivate), "active"] = True

                df.to_csv(PROCESSED_IP_FILE, index=False)
            print("csv file is up to date")
            return
        
        print("creating a new csv file...")
        df = (pd.read_csv(RAW_FILE, header=None, skip_blank_lines=True, names=["ip"]).drop_duplicates().reset_index(drop=True))
        df["active"] = True
        df['stix_id'] = None
        df['score'] = -1
        df['tags'] = None
        df["upload_date"] = None

        df.to_csv(PROCESSED_IP_FILE, index=False)
        if return_csv:return df