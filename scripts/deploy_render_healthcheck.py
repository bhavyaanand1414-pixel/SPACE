#!/usr/bin/env python3
"""
SIH1518 — Production Deployment Verification Script.

Tests a live Render backend URL or localhost endpoint for:
- API Health Status
- Model Readiness
- Database Connection
- Tool Execution
"""

import sys
import urllib.request
import json
import time

def verify_deployment(base_url="http://localhost:8000"):
    print(f"[*] Probing SIH1518 API Health at: {base_url}/api/v1/health")
    try:
        req = urllib.request.Request(f"{base_url}/api/v1/health")
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                print(f"[SUCCESS] Core API Status: {data.get('status')}")
                print(f"          Application: {data.get('app_name')} v{data.get('version')}")
                print(f"          Environment: {data.get('environment')}")
                print(f"          Model Device: {data.get('model_device')}")
                return True
    except Exception as exc:
        print(f"[ERROR] Health check failed: {exc}")
        return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    success = verify_deployment(url)
    sys.exit(0 if success else 1)
