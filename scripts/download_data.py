import os
import hashlib
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
EXPECTED_FILE = "USAID_GHSC_PSM_Health_Commodity_Delivery_Dataset.csv"
EXPECTED_SHA256 = "df9d65337ef30ebf62f32380068d53012975737c366f188cbccb2ddd79b0a83a".lower()

def get_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest().lower()

def main():
    target_path = os.path.join(DATA_DIR, EXPECTED_FILE)
    
    if not os.path.exists(target_path):
        print(f"ERROR: Dataset not found at {target_path}")
        print("Please download the dataset manually and place it in the data/ directory.")
        print("Official Data.gov catalog landing page:")
        print("https://catalog.data.gov/dataset/usaid-ghsc-psm-health-commodity-delivery-dataset")
        print("Refer to data/README.md for detailed instructions.")
        sys.exit(1)
        
    print(f"Found dataset at {target_path}. Verifying checksum...")
    actual_hash = get_sha256(target_path)
    
    if actual_hash == EXPECTED_SHA256:
        print(f"SUCCESS: Checksum verified ({actual_hash}).")
        print("The dataset matches the exact version used in the final study.")
    else:
        print(f"WARNING: Checksum mismatch!")
        print(f"Expected: {EXPECTED_SHA256}")
        print(f"Actual:   {actual_hash}")
        print("The dataset may have been updated upstream. This might cause numerical drift compared to the final paper.")
        sys.exit(2)

if __name__ == "__main__":
    main()
