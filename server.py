import json, os, re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import urllib.request

RPC=os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com")
B58=re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

def rpc(method, params):
    data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(RPC,data=data,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=12) as r:
        return json.loads(r.read())

def scan(mint):
    if not B58.match(mint): raise ValueError("Invalid Solana mint address.")
    acc=rpc("getAccountInfo",[mint,{"encoding":"jsonParsed","commitment":"finalized"}])
    if not acc.get("result",{}).get("value"): raise ValueError("Mint account not found.")
    info=acc["result"]["value"]["data"]["parsed"]["info"]
    supply=rpc("getTokenSupply",[mint,{"commitment":"finalized"}])["result"]["value"]
    largest=rpc("getTokenLargestAccounts",[mint,{"commitment":"finalized"}])["result"]["value"]
    decimals=int(supply["decimals"]); total=float(supply["uiAmountString"] or 0)
    top=sum(float(x["uiAmountString"] or 0) for x in largest)
    concentration=(top/total*100) if total else 0
    mint_auth=info.get("mintAuthority")
    freeze_auth=info.get("freezeAuthority")
    score=0; checks={}
    if mint_auth: score+=15; checks["Mint authority"]={"status":"warning","message":"Active"}
    else: checks["Mint authority"]={"status":"ok","message":"Revoked"}
    if freeze_auth: score+=15; checks["Freeze authority"]={"status":"warning","message":"Active"}
    else: checks["Freeze authority"]={"status":"ok","message":"Revoked"}
    if concentration>=80: score+=35; msg=f"Top 20 accounts ≈ {concentration:.1f}%"
    elif concentration>=50: score+=20; msg=f"Top 20 accounts ≈ {concentration:.1f}%"
    else: score+=5; msg=f"Top 20 accounts ≈ {concentration:.1f}%"
    checks["Holder concentration"]={"status":"warning" if concentration>=50 else "ok","message":msg}
    checks["Total supply"]={"status":"ok","message":f"{supply['uiAmountString']} (decimals {decimals})"}
    checks["Program"]={"status":"ok","message":"Solana token mint found"}
    return {"mint":mint,"riskScore":min(score,100),"checks":checks}

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=="/api/scan":
            try:
                mint=parse_qs(u.query).get("mint",[""])[0]
                out=scan(mint); self.send_response(200)
            except Exception as e:
                out={"error":str(e)}; self.send_response(400)
            self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(json.dumps(out).encode());return
        if u.path=="/" or u.path=="/index.html":
            data=open("site/index.html","rb").read();self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(data);return
        self.send_response(404);self.end_headers()
if __name__=="__main__": print("NIN running on http://localhost:8080");HTTPServer(("0.0.0.0",8080),H).serve_forever()
