"""
Freshworks CRM — Aadhaar Upload Automation

Usage:
    python main.py --cookie "COOKIE_VALUE" --csrf "CSRF_TOKEN"
"""

import argparse
import os
import sys

from logger import log
from api_client import FreshworksClient
from pdf_converter import convert_pdf_to_images
from processor import process_person, print_summary, human_delay

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(WORK_DIR, "Aadhar.pdf")
NAMES_PATH = os.path.join(WORK_DIR, "aadhar.txt")
IMAGE_DIR = os.path.join(WORK_DIR, "image")


def main():
    parser = argparse.ArgumentParser(description="Freshworks Aadhaar Upload")
    parser.add_argument("--cookie", required=True, help="Cookie header from browser")
    parser.add_argument("--csrf", required=True, help="X-CSRF-Token header from browser")
    args = parser.parse_args()

    log.header("Freshworks Aadhaar Upload Automation")

    # Validate inputs
    for path, label in [(NAMES_PATH, "aadhar.txt"), (PDF_PATH, "Aadhar.pdf")]:
        if not os.path.exists(path):
            log.error(f"{label} not found: {path}")
            sys.exit(1)

    with open(NAMES_PATH, "r") as f:
        names = [line.strip() for line in f if line.strip()]
    log.info(f"Loaded {len(names)} names")

    # Convert PDF pages to images
    log.header("Converting PDF to Images")
    image_paths = convert_pdf_to_images(PDF_PATH, names, IMAGE_DIR)
    log.success(f"{len(image_paths)} images ready")

    # Verify auth
    log.header("Verifying Authentication")
    client = FreshworksClient(args.cookie, args.csrf)
    try:
        test = client.search(names[0])
        if "search_response" not in test:
            log.error(f"Bad response: {str(test)[:200]}")
            sys.exit(1)
        log.success("Auth OK")
    except Exception as e:
        log.error(f"Auth failed: {e}")
        sys.exit(1)

    # Process each person
    summary = []
    for i, (name, img) in enumerate(zip(names, image_paths)):
        result = process_person(client, name, img, i + 1, len(names))
        summary.append(result)
        if i < len(names) - 1:
            human_delay()

    print_summary(summary)


if __name__ == "__main__":
    main()
