import json
import os
import re
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs


RPC = os.getenv(
    "SOLANA_RPC_URL",
    "https://api.mainnet-beta.solana.com"
)

B58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def rpc(method, params):
    data = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }).encode()

    req = urllib.request.Request(
        RPC,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode())


def scan(mint):
    if not B58.match(mint):
        raise ValueError("Invalid Solana mint address")

    account = rpc(
        "getAccountInfo",
        [
            mint,
            {
                "encoding": "jsonParsed"
            }
        ]
    )

    value = account.get("result", {}).get("value")

    if not value:
        raise ValueError("Mint account not found")

    parsed = value.get("data", {}).get("parsed", {})
    info = parsed.get("info", {})

    supply = rpc(
        "getTokenSupply",
        [
            mint,
            {
                "commitment": "confirmed"
            }
        ]
    )

    largest = rpc(
        "getTokenLargestAccounts",
        [
            mint,
            {
                "commitment": "confirmed"
            }
        ]
    )

    supply_value = supply.get("result", {}).get("value", {})
    largest_accounts = largest.get("result", {}).get("value", [])

    decimals = int(supply_value.get("decimals", 0))
    total_amount = float(
        supply_value.get("uiAmountString") or
        supply_value.get("uiAmount") or
        0
    )

    top_amount = sum(
        float(account.get("uiAmountString") or 0)
        for account in largest_accounts[:20]
    )

    concentration = (
        top_amount / total_amount * 100
        if total_amount > 0
        else 0
    )

    mint_authority = info.get("mintAuthority")
    freeze_authority = info.get("freezeAuthority")

    score = 0
    checks = {}

    if mint_authority:
        score += 15
        checks["Mint authority"] = {
            "status": "warning",
            "message": "Mint authority is active"
        }
    else:
        checks["Mint authority"] = {
            "status": "ok",
            "message": "Mint authority is disabled"
        }

    if freeze_authority:
        score += 15
        checks["Freeze authority"] = {
            "status": "warning",
            "message": "Freeze authority is active"
        }
    else:
        checks["Freeze authority"] = {
            "status": "ok",
            "message": "Freeze authority is disabled"
        }

    if concentration >= 80:
        score += 35
        concentration_message = (
            f"Top 20 accounts hold approximately "
            f"{concentration:.2f}% of supply"
        )
        concentration_status = "danger"

    elif concentration >= 50:
        score += 20
        concentration_message = (
            f"Top 20 accounts hold approximately "
            f"{concentration:.2f}% of supply"
        )
        concentration_status = "warning"

    else:
        score += 5
        concentration_message = (
            f"Top 20 accounts hold approximately "
            f"{concentration:.2f}% of supply"
        )
        concentration_status = "ok"

    checks["Holder concentration"] = {
        "status": concentration_status,
        "message": concentration_message
    }

    checks["Total supply"] = {
        "status": "ok",
        "message": f"Total supply: {total_amount}"
    }

    checks["Program"] = {
        "status": "ok",
        "message": parsed.get("type", "SPL Token")
    }

    return {
        "mint": mint,
        "riskScore": min(score, 100),
        "decimals": decimals,
        "totalSupply": total_amount,
        "top20Concentration": round(concentration, 2),
        "checks": checks
    }


class Handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, filepath):
        try:
            with open(filepath, "rb") as file:
                data = file.read()

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(data))
            )
            self.end_headers()
            self.wfile.write(data)

        except FileNotFoundError:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"index.html not found")

    def do_GET(self):
        url = urlparse(self.path)

        if url.path == "/api/scan":
            try:
                mint = parse_qs(url.query).get("mint", [""])[0]

                result = scan(mint)

                self.send_json(200, result)

            except Exception as error:
                self.send_json(
                    400,
                    {
                        "error": str(error)
                    }
                )

            return

        if url.path == "/" or url.path == "/index.html":
            self.send_file("site/index.html")
            return

        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Not found")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))

    server = ThreadingHTTPServer(
        ("0.0.0.0", port),
        Handler
    )

    print(f"NIN running on port {port}")

    server.serve_forever()
