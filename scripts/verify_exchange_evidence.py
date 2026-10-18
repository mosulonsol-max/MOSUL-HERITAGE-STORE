#!/usr/bin/env python3
"""Read-only exchange listing evidence collection. No private keys or transactions."""
import datetime, json, os, urllib.request, urllib.error, time
from pathlib import Path

MINT="6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump"
CREATOR="EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu"
RPC=os.environ.get("SOLANA_RPC_URL","").strip() or "https://api.mainnet-beta.solana.com"
REPORT={"timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mint":MINT,"creator_wallet":CREATOR,"sources":{},"errors":[],"limitations":[]}
if not os.environ.get("SOLANA_RPC_URL","").strip():
    REPORT["limitations"].append("SOLANA_RPC_URL secret is not configured; using the shared public Solana RPC, which may return HTTP 403/429.")

def fetch(url,payload=None):
    body=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(url,data=body,headers={"User-Agent":"MOSUL-ReadOnly-Verification/1.0","Accept":"application/json","Content-Type":"application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=18) as response:
                return json.load(response)
        except urllib.error.HTTPError as e:
            if e.code not in (429,500,502,503,504) or attempt==2:
                raise
            time.sleep(2*(attempt+1))

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
    try:
        v=rpc("getTokenLargestAccounts",[MINT,{"commitment":"finalized"}])
    except Exception as first_error:
        alternatives=["https://solana-rpc.publicnode.com","https://solana.drpc.org"]
        v=None
        for endpoint in alternatives:
            try:
                j=fetch(endpoint,{"jsonrpc":"2.0","id":1,"method":"getTokenLargestAccounts","params":[MINT,{"commitment":"finalized"}]})
                if "error" in j: raise RuntimeError(str(j["error"]))
                v=j["result"]
                REPORT["limitations"].append("Largest token accounts retrieved from fallback public Solana RPC: "+endpoint)
                break
            except Exception as e:
                REPORT["errors"].append({"source":"top_accounts_fallback","endpoint":endpoint,"error":str(e)[:200]})
        if v is None: raise RuntimeError("All RPC providers failed; initial: "+str(first_error)[:160])
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

def gecko_pools():
    url="https://api.geckoterminal.com/api/v2/networks/solana/tokens/"+MINT+"/pools"
    j=fetch(url)
    out=[]
    for p in j.get("data",[]):
        a=p.get("attributes") or {}
        out.append({"pool_id":p.get("id"),"address":a.get("address"),"name":a.get("name"),
                    "reserve_usd":a.get("reserve_in_usd"),"volume_usd":a.get("volume_usd"),
                    "base_token_price_usd":a.get("base_token_price_usd"),"pool_created_at":a.get("pool_created_at")})
    REPORT["limitations"].append("GeckoTerminal pools may differ from DexScreener; pool reserve is not necessarily executable liquidity.")
    return out

def pumpfun_coin():
    # GeckoTerminal's documented token endpoint reports Pump.fun launchpad details
    # for bonding-curve tokens and avoids undocumented frontend-api endpoints.
    url="https://api.geckoterminal.com/api/v2/networks/solana/tokens/"+MINT
    j=fetch(url)
    data=j.get("data") or {}
    fields=data.get("attributes") or {}
    if fields.get("address") != MINT:
        raise ValueError("GeckoTerminal token response did not match the configured mint")
    return {"provider":"GeckoTerminal public API","source_url":url,"fields":fields}

def gecko_token_info():
    # Additional metadata, security signals, developer holdings, and optional
    # holder statistics. Null fields stay null; this is not a substitute for RPC.
    url="https://api.geckoterminal.com/api/v2/networks/solana/tokens/"+MINT+"/info"
    j=fetch(url)
    data=j.get("data") or {}
    fields=data.get("attributes") or {}
    if fields.get("address") != MINT:
        raise ValueError("GeckoTerminal token-info response did not match the configured mint")
    return {"provider":"GeckoTerminal public API","source_url":url,"fields":fields}

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
capture("gecko_pools",gecko_pools)
capture("pumpfun_coin",pumpfun_coin)
capture("gecko_token_info",gecko_token_info)
capture("signature_page_https",website)
REPORT["limitations"].extend([
"Explorer creator labels are not cryptographic evidence of legal project ownership.",
"A wallet-control signature has been independently verified and published at docs/MOSUL-WALLET-PROOF-VERIFIED-2026-10-17.json; this job does not verify legal identity.",
"Founder/team allocation, related-wallet clusters, locks, vesting and beneficial ownership cannot be inferred from the top-account list alone.",
"Even if HTTPS page loads, Phantom iPhone signing and end-to-end UX require manual testing.",
"No application is submitted by this workflow.",
"GeckoTerminal public API is beta and rate-limited; absent or null fields remain unverified rather than being inferred.",
"GeckoTerminal holder statistics may be null or incomplete; token-account concentration still requires a working Solana RPC or a documented holder-data provider.",
"Pump.fun launchpad state is reported from GeckoTerminal’s token endpoint; verify material trading or migration claims against on-chain state."
])
def completeness_status():
    sources=REPORT["sources"]
    missing=[]
    if "largest_token_accounts" not in sources:
        missing.append("largest token accounts and token-account concentration")
    info=(sources.get("gecko_token_info") or {}).get("fields") or {}
    holders=info.get("holders") or {}
    if holders.get("count") is None or holders.get("distribution_percentage") is None:
        missing.append("holder count and holder distribution")
    launchpad=((sources.get("pumpfun_coin") or {}).get("fields") or {}).get("launchpad_details")
    if not isinstance(launchpad,dict) or "completed" not in launchpad:
        missing.append("Pump.fun graduation and migration state")
    dex_pairs_found=bool(sources.get("dex_pairs"))
    gecko_pools_found=bool(sources.get("gecko_pools"))
    if not dex_pairs_found and not gecko_pools_found:
        missing.append("independently identified DEX pool")
    market_fields=(sources.get("pumpfun_coin") or {}).get("fields") or {}
    if market_fields.get("price_usd") is None and not any(
        pool.get("base_token_price_usd") is not None for pool in sources.get("gecko_pools",[])
    ):
        missing.append("current pool price")
    return {
        "status":"partial" if missing else "complete",
        "missing_fields":missing,
        "observed_volume_24h_usd":market_fields.get("volume_usd",{}).get("h24"),
        "note":"A measured zero volume is reported as zero; it is not treated as missing data."
    }

REPORT["completeness"]=completeness_status()
Path("exchange-evidence.json").write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"timestamp_utc":REPORT["timestamp_utc"],
    "sources_successful":list(REPORT["sources"]),
    "errors":REPORT["errors"],
    "completeness":REPORT["completeness"],
    "pairs_found":len(REPORT["sources"].get("dex_pairs",[])),
    "https_page":REPORT["sources"].get("signature_page_https"),
    "report_file":"exchange-evidence.json"},indent=2))

# Actionable exchange diligence summary in job logs; raw source data remains in artifact.
supply=REPORT["sources"].get("token_supply",{}).get("value",{})
accounts=REPORT["sources"].get("largest_token_accounts",[])
total=int(supply.get("amount") or 0)
top20=sum(int(account.get("amount") or 0) for account in accounts)
pairs=REPORT["sources"].get("dex_pairs",[])
print("LISTING_EVIDENCE_SUMMARY="+json.dumps({
 "timestamp_utc":REPORT["timestamp_utc"],
 "mint":MINT,
 "supply":supply.get("uiAmountString"),
 "decimals":supply.get("decimals"),
 "top20_token_account_share_pct":round(top20/total*100,4) if total and "largest_token_accounts" in REPORT["sources"] else None,
 "top20_are_not_beneficial_owners":True,
 "largest_accounts_status":"verified" if "largest_token_accounts" in REPORT["sources"] else "unavailable",
 "dex_pair_count":len(pairs),
 "gecko_pool_count":len(REPORT["sources"].get("gecko_pools",[])),
 "gecko_pools":REPORT["sources"].get("gecko_pools"),
 "pumpfun_coin":REPORT["sources"].get("pumpfun_coin"),
 "gecko_token_info":REPORT["sources"].get("gecko_token_info"),
 "dex_pairs":[{"dex":p.get("dexId"),"pair":p.get("pairAddress"),"liquidity_usd":(p.get("liquidity") or {}).get("usd"),"volume_24h":(p.get("volume") or {}).get("h24"),"price_usd":p.get("priceUsd")} for p in pairs],
 "website":REPORT["sources"].get("signature_page_https"),
 "errors":REPORT["errors"]
},ensure_ascii=False))
