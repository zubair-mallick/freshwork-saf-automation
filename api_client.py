"""Freshworks CRM API client."""

import os
import requests

BASE_URL = "https://sundirect-606378453475310199.myfreshworks.com"
OWNER_ID = 403000001694

class FreshworksClient:
    def __init__(self, cookie, csrf_token):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRF-Token": csrf_token,
            "Cookie": cookie,
        })

    def _request(self, method, path, **kwargs):
        resp = self.session.request(method, f"{BASE_URL}{path}", **kwargs)
        if resp.status_code == 401 or "login" in resp.text.lower()[:100]:
            raise Exception("Session expired — grab fresh Cookie and X-CSRF-Token from browser")
        return resp

    def search(self, name):
        payload = {
            "q": name,
            "include": "all",
            "g": "1",
            "per_page": 100,
            "filter_rules": [{"field": "owner_id", "value": [OWNER_ID], "operator": "is"}],
        }
        resp = self._request("POST", "/crm/sales/global_search",
                             json=payload,
                             headers={"Content-Type": "application/json; charset=utf-8"})
        resp.raise_for_status()
        return resp.json()

    def get_account(self, account_id):
        resp = self._request("GET", f"/crm/sales/custom_module/cm_accounts/{account_id}?include=territory")
        resp.raise_for_status()
        return resp.json()

    def upload_document(self, file_path, account_id):
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, "image/png")}
            data = {
                "file_name": file_name,
                "targetable_id": str(account_id),
                "targetable_type": "cm_accounts",
                "is_shared": "false",
                "tags": "ID Proof",
            }
            resp = self._request("POST", "/crm/sales/documents", files=files, data=data)
        resp.raise_for_status()
        return resp.json()

    def update_file_uploaded(self, account_id):
        payload = {"cm_accounts": {"custom_field": {"cf_file_uploaded": True}}}
        resp = self._request("PUT", f"/crm/sales/custom_module/cm_accounts/{account_id}",
                             json=payload,
                             headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        return resp.json()
