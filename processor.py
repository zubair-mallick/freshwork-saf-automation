"""Core logic — process each person through the 4-step workflow."""

import os
from logger import log, Logger, _write, LOG_FILE


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
        return {"name": name, "status": "NO_MATCH", "reason": str(e)}

    results = data.get("search_response", [])
    cm_accounts = [r for r in results if r.get("type") == "cm_accounts"]
    matched = [r for r in cm_accounts if names_match(name, r.get("name", ""))]

    log.info(f"Results: {len(results)} total, {len(cm_accounts)} cm_accounts, {len(matched)} name-matched")

    if not matched:
        log.warn("No matching accounts found")
        return {"name": name, "status": "NO_MATCH", "reason": "No matching cm_accounts"}

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

    succeeded = sum(1 for r in account_results if r["status"] == "SUCCESS")
    return {"name": name, "status": "DONE", "succeeded": succeeded, "details": account_results}


def print_summary(summary):
    log.header("RESULTS — Per Person")

    total_s = total_sk = total_no = total_f = 0
    G, R, Y, X, B, D = Logger.G, Logger.R, Logger.Y, Logger.X, Logger.B, Logger.D

    for i, r in enumerate(summary):
        idx = f"[{i+1}/{len(summary)}]"
        name = r["name"]

        if r["status"] == "NO_MATCH":
            total_no += 1
            _write(f"  {R}{idx}{X} {B}{name}{X} — {R}No Matching Accounts{X}")

        elif r["status"] == "FAILED":
            total_f += 1
            _write(f"  {R}{idx}{X} {B}{name}{X} — {R}FAILED: {r.get('reason','')}{X}")

        elif r["status"] == "DONE":
            details = r.get("details", [])
            s = sum(1 for d in details if d["status"] == "SUCCESS")
            sk = sum(1 for d in details if d["status"] == "SKIPPED")
            f = sum(1 for d in details if d["status"] in ("FAILED", "PARTIAL"))
            total_s += s
            total_sk += sk
            total_f += f

            if s > 0 and f == 0:
                _write(f"  {G}{idx}{X} {B}{name}{X} — {G}{s} uploaded{X}, {sk} skipped")
            elif s > 0 and f > 0:
                _write(f"  {Y}{idx}{X} {B}{name}{X} — {G}{s} uploaded{X}, {R}{f} failed{X}, {sk} skipped")
            elif s == 0 and sk > 0:
                _write(f"  {Y}{idx}{X} {B}{name}{X} — {Y}All {sk} skipped{X}")
            else:
                _write(f"  {R}{idx}{X} {B}{name}{X} — {R}{f} failed{X}")

            for d in details:
                if d["status"] == "SUCCESS":
                    _write(f"      {G}SUCCESS{X} Account {d['id']} (doc:{d['doc_id']})")
                elif d["status"] == "SKIPPED":
                    _write(f"      {Y}SKIPPED{X} Account {d['id']} ({d.get('reason','')})")
                else:
                    _write(f"      {R}{d['status']}{X} Account {d['id']} ({d.get('reason','')})")

    # Final counts
    _write(f"\n{'='*70}")
    _write(f"  {B}FINAL COUNTS{X}")
    _write(f"{'='*70}")
    _write(f"  Total people processed : {len(summary)}")
    _write(f"  {G}Accounts uploaded       : {total_s}{X}")
    _write(f"  {Y}Accounts skipped        : {total_sk}{X}")
    _write(f"  {R}No matching accounts    : {total_no}{X}")
    _write(f"  {R}Failed                  : {total_f}{X}")
    _write(f"{'='*70}")
    _write(f"  Log saved to: {LOG_FILE}")
    _write(f"{'='*70}\n")
