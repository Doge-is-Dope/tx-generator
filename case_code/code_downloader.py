import os
import requests
import json
import base64
from dotenv import load_dotenv
from tqdm import tqdm
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from case_code import OUTPUT_DIR, RAW_OUTPUT_DIR, METADATA_OUTPUT_PATH


class CodeDownloader:
    def __init__(self, is_dev: bool = True, output_dir: str = RAW_OUTPUT_DIR):
        load_dotenv()
        self.is_dev: bool = is_dev
        self.access_token: str = os.getenv("GITHUB_ACCESS_TOKEN")
        self.repo: str = "blocto/bento-interface"
        self.branch: str = "develop" if self.is_dev else "main"
        self.github_api_url: str = "https://api.github.com"
        self.output_dir: str = output_dir

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.access_token}",
        }

    def _get_case_path(self) -> list[str]:
        """Get all case paths from the repository."""
        base_url = (
            f"{self.github_api_url}/repos/{self.repo}/git/trees/"
            f"{self.branch}?recursive=1"
        )
        response = requests.get(base_url, headers=self.headers)
        response.raise_for_status()
        all_files = response.json()["tree"]
        return [
            file["path"]
            for file in all_files
            if file["path"].startswith("cases/")
            and file["path"].endswith(".ts")
            and len(file["path"].split("/")) > 2
        ]

    def _download_file(self, file_info: dict, path: str) -> None:
        """Download a single file from the repository."""
        content_encoded = file_info["content"]
        file_content = base64.b64decode(content_encoded)

        with open(os.path.join(self.output_dir, path), "wb") as f:
            f.write(file_content)

    def _download_single_case(self, path, base_url):
        local_dir = os.path.dirname(os.path.join(self.output_dir, path))
        os.makedirs(local_dir, exist_ok=True)
        url = f"{base_url}/{path}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        file_info = response.json()
        self._download_file(file_info, path)

    def _download_metadata(self, total_downloads: int) -> None:
        """Download the metadata file from the repository."""
        import json
        import time
        import csv

        env = "dev" if self.is_dev else "release"
        url = f"https://bento-batch-{env}.netlify.app/case/api/meta"
        response = requests.get(url)
        response.raise_for_status()
        cases = response.json()["cases"]

        metadata: Dict = {}
        # Sort the cases by id alphabetically
        metadata["cases"] = cases_sorted = sorted(cases, key=lambda case: case["id"])
        metadata["total_cases"] = len(cases_sorted)
        metadata["total_downloads"] = total_downloads
        metadata["last_updated"] = int(time.time())

        # Write the metadata to a file in 'raw_data/'
        with open(os.path.join(self.output_dir, METADATA_OUTPUT_PATH), "w") as f:
            json.dump(metadata, f)

        with open(os.path.join(self.output_dir, "cases.csv"), "w") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "transformable"])
            for case in cases_sorted:
                writer.writerow([case["id"], False])

    def download(self) -> None:
        """Download the source code for all Bento cases from the repository."""
        case_paths = self._get_case_path()
        base_url = f"{self.github_api_url}/repos/{self.repo}/contents"

        # Check if output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Use a session for requests
        with requests.Session() as session:
            session.headers.update(self.headers)
            futures = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                for path in case_paths:
                    futures.append(
                        executor.submit(self._download_single_case, path, base_url)
                    )
                for future in tqdm(
                    as_completed(futures),
                    total=len(case_paths),
                    desc=f"Downloading {self.branch} branch files",
                    unit="file",
                ):
                    future.result()

        # Download metadata
        self._download_metadata(total_downloads=len(case_paths))


def get_metadata():
    file_path = os.path.join(RAW_OUTPUT_DIR, METADATA_OUTPUT_PATH)
    if not os.path.exists(file_path):
        raise FileNotFoundError("Not found. Call CodeDownloader().download() first.")
    with open(file_path, "r") as f:
        metadata = json.load(f)
    return metadata


if __name__ == "__main__":
    downloader = CodeDownloader(is_dev=False)
    downloader.download()

    metadata = get_metadata()
    print(f"{'Total cases:':<14} {metadata['total_cases']}")

    from datetime import datetime

    # Convert timestamp to datetime object
    dt_obj = datetime.fromtimestamp(metadata["last_updated"])
    readable_str = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
    print(f"{'Last updated:':<14} {readable_str}")
