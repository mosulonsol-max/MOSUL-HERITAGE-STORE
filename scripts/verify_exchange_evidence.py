#!/usr/bin/env python3
"""Read-only exchange listing evidence collection. No private keys or transactions."""
import datetime, json, os, urllib.request, urllib.error
from pathlib import Path

MINT="6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump"
CREATOR="EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu"
RPC=os.environ.get("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com")
REPORT={"timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mint":MINT,"creator_wallet":CREATOR,"sources":{},"errors":[],"limitations":[]}

def fetch(url,payload=None):
    body=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(url,data=body,headers={"User-Agent":"MOSUL-ReadOnly-Verification/1.0","Accept":"application/json","Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=18) as response:
        return json.load(response)

def rpc(method,params):
    j=fetch(RPC,{"jsonrpc":"2.0","id":1,"method":method,"params":params})
    if "error" in j: raise RuntimeError(str(j["error"]))
    return j["result"]

def capture(label,fn):
    try: REPORT["sources"][label]=fn()
    except Exception as e: REPORT["errors"].append({"source":label,"error":str(e)[:400]})

def token_supply():
    return rpc("getTokenSupply",[MINT,{"commitment":"finalized"}])

def mint_account():
    v=rpc("getAccountInfo",[MINT,{"encoding":"jsonParsed","commitment":"finalized"}])
    return v.get("value") if v else None

def top_accounts():
    v=rpc("getTokenLargestAccounts",[MINT,{"commitment":"finalized"}])
    accounts=v.get("value",[])
    REPORT["limitations"].append("Top 20 token accounts are NOT top 20 beneficial owners. LP vaults, exchange custody and wallets may own multiple token accounts.")
    return accounts

def creator_tokens():
    # Owner balances of the publicly identified creator wallet; not necessarily all project-controlled wallets.
    return rpc("getTokenAccountsByOwner",[CREATOR,{"mint":MINT},{"encoding":"jsonParsed","commitment":"finalized"}])

def dex_pairs():
    j=fetch("https://api.dexscreener.com/latest/dex/tokens/"+MINT)
    pairs=[p for p in (j.get("pairs") or []) if p.get("chainId")=="solana" and (p.get("baseToken",{}).get("address")==MINT or p.get("quoteToken",{}).get("address")==MINT)]
    out=[]
    for p in pairs:
        out.append({"dexId":p.get("dexId"),"pairAddress":p.get("pairAddress"),"url":p.get("url"),
                    "baseToken":p.get("baseToken"),"quoteToken":p.get("quoteToken"),
                    "liquidity":p.get("liquidity"),"volume":p.get("volume"),
                    "txns":p.get("txns"),"priceUsd":p.get("priceUsd"),"fdv":p.get("fdv"),
                    "marketCap":p.get("marketCap"),"pairCreatedAt":p.get("pairCreatedAt")})
    REPORT["limitations"].append("DEX Screener liquidity and 24h volume are per-pool estimates and may not cover all venues. Do not sum duplicate pools or confuse FDV with market cap.")
    return out

def website():
    url="https://mosulonsol-max.github.io/MOSUL-HERITAGE-STORE/wallet-proof.html"
    req=urllib.request.Request(url,headers={"User-Agent":"MOSUL-ReadOnly-Verification/1.0"})
    with urllib.request.urlopen(req,timeout=18) as resp:
        data=resp.read(300000).decode("utf-8","replace")
        return {"url":resp.geturl(),"http_status":resp.status,
                "expected_page_present":("Wallet ownership statement" in data and "wallet-proof.js" in data)}
capture("token_supply",token_supply)
capture("mint_account",mint_account)
capture("largest_token_accounts",top_accounts)
capture("creator_wallet_token_accounts",creator_tokens)
capture("dex_pairs",dex_pairs)
capture("signature_page_https",website)
REPORT["limitations"].extend([
"Explorer creator labels are not cryptographic evidence of legal project ownership.",
"An actual wallet message signature is still required; this job does not sign or verify an owner's message.",
"Founder/team allocation, related-wallet clusters, locks, vesting and beneficial ownership cannot be inferred from the top-account list alone.",
"Even if HTTPS page loads, Phantom iPhone signing and end-to-end UX require manual testing.",
"No application is submitted by this workflow."
])
Path("exchange-evidence.json").write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"timestamp_utc":REPORT["timestamp_utc"],
    "sources_successful":list(REPORT["sources"]),
    "errors":REPORT["errors"],
    "pairs_found":len(REPORT["sources"].get("dex_pairs",[])),
    "https_page":REPORT["sources"].get("signature_page_https"),
    "report_file":"exchange-evidence.json"},indent=2))
