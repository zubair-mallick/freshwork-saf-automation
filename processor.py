"""Core logic — process each person through the 4-step workflow."""

import os
import time
import sys
from logger import log, Logger

COOLDOWN = 10  # seconds between each account cycle to mimic human pace


def human_delay():
    for i in range(COOLDOWN, 0, -1):
        sys.stdout.write(f"\r    Waiting {i}s before next...")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 40 + "\r")
    sys.stdout.flush()


def names_match(search_name, result_name):
    return search_name.strip().upper() == result_name.strip().upper()


def process_person(client, name, image_path, index, total):
    log.header(f"[{index}/{total}] {name}")

    # Step 1: Search
    log.step(1, f'Searching "{name}"...')
    try:
        data = client.search(name)
    except Exception as e:
        log.error(f"Search failed: {e}")
        return {"name": name, "status": "FAILED", "reason": str(e)}

    results = data.get("search_response", [])
    cm_accounts = [r for r in results if r.get("type") == "cm_accounts"]
    matched = [r for r in cm_accounts if names_match(name, r.get("name", ""))]

    log.info(f"Results: {len(results)} total, {len(cm_accounts)} cm_accounts, {len(matched)} name-matched")

    if not matched:
        log.warn("No matching accounts — skipping")
        return {"name": name, "status": "SKIPPED", "reason": "No matching cm_accounts"}

    # Step 2/3/4 for each matched account
    account_results = []
    for acc in matched:
        acc_id = acc["id"]

        # Step 2: Check SAF status
        log.step(2, f"Checking account {acc_id}...")
        try:
            acc_data = client.get_account(acc_id)
        except Exception as e:
            log.error(f"Fetch failed: {e}")
            account_results.append({"id": acc_id, "status": "FAILED", "reason": str(e)})
            continue

        cf = acc_data.get("cm_accounts", {}).get("custom_field", {})
        saf_status = cf.get("cf_saf_status")
        file_uploaded = cf.get("cf_file_uploaded")
        log.result("SAF Status", saf_status)
        log.result("File Uploaded", file_uploaded)

        if saf_status != "Pending SAF with DT":
            log.warn(f'SAF status is "{saf_status}" — skipping')
            account_results.append({"id": acc_id, "status": "SKIPPED", "reason": f"SAF: {saf_status}"})
            continue

        if file_uploaded:
            log.warn("File already uploaded — skipping")
            account_results.append({"id": acc_id, "status": "SKIPPED", "reason": "Already uploaded"})
            continue

        log.success("Eligible for upload")

        # Step 3: Upload image
        log.step(3, f"Uploading {os.path.basename(image_path)} -> account {acc_id}...")
        try:
            upload_resp = client.upload_document(image_path, acc_id)
            doc_id = upload_resp.get("id")
            log.success(f"Uploaded — Document ID: {doc_id}")
        except Exception as e:
            log.error(f"Upload failed: {e}")
            account_results.append({"id": acc_id, "status": "FAILED", "reason": str(e)})
            continue

        # Step 4: Update flag
        log.step(4, f"Setting cf_file_uploaded = true for {acc_id}...")
        try:
            update_resp = client.update_file_uploaded(acc_id)
            flag = update_resp.get("cm_accounts", {}).get("custom_field", {}).get("cf_file_uploaded")
            log.success(f"Updated — cf_file_uploaded: {flag}")
            account_results.append({"id": acc_id, "status": "SUCCESS", "doc_id": doc_id})
        except Exception as e:
            log.error(f"Update failed (image uploaded as doc {doc_id}): {e}")
            account_results.append({"id": acc_id, "status": "PARTIAL", "reason": str(e), "doc_id": doc_id})

        # Cooldown between accounts
        if acc != matched[-1]:
            human_delay()

    succeeded = sum(1 for r in account_results if r["status"] == "SUCCESS")
    return {"name": name, "status": "DONE", "succeeded": succeeded, "details": account_results}


def print_summary(summary):
    log.header("SUMMARY")
    total_s = total_sk = total_f = 0

    for r in summary:
        name = r["name"]
        if r["status"] == "DONE":
            details = r.get("details", [])
            s = sum(1 for d in details if d["status"] == "SUCCESS")
            sk = sum(1 for d in details if d["status"] == "SKIPPED")
            f = sum(1 for d in details if d["status"] in ("FAILED", "PARTIAL"))
            total_s += s
            total_sk += sk
            total_f += f
            log.line(f"{Logger.B}{name}{Logger.X}: {s} uploaded, {sk} skipped, {f} failed")
            for d in details:
                color = Logger.G if d["status"] == "SUCCESS" else Logger.Y if d["status"] == "SKIPPED" else Logger.R
                extra = f" (doc:{d['doc_id']})" if d.get("doc_id") else f" ({d.get('reason','')})"
                log.line(f"    {color}{d['status']}{Logger.X} Account {d['id']}{extra}")
        elif r["status"] == "SKIPPED":
            total_sk += 1
            log.line(f"{Logger.Y}{name}{Logger.X}: SKIPPED — {r.get('reason','')}")
        else:
            total_f += 1
            log.line(f"{Logger.R}{name}{Logger.X}: FAILED — {r.get('reason','')}")

    print(f"\n{'─'*70}")
    print(f"  Total: {Logger.G}{total_s} uploaded{Logger.X} | {Logger.Y}{total_sk} skipped{Logger.X} | {Logger.R}{total_f} failed{Logger.X}")
    print(f"{'─'*70}\n")
