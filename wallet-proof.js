'use strict';
// No remote requests, third-party libraries, transaction or token transfer code.
const EXPECTED = 'EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu';
const MESSAGE = [
  'MOSUL HERITAGE — PUBLIC TOKEN ASSOCIATION STATEMENT',
  'Date: 2026-10-17',
  'Network: Solana Mainnet',
  'Project: MOSUL HERITAGE',
  'Token: MOSUL',
  'Token mint: 6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump',
  'Signing wallet: ' + EXPECTED,
  '',
  'I am authorized to represent MOSUL HERITAGE. I confirm that MOSUL HERITAGE publicly identifies the token mint above as its MOSUL token and that I control the signing wallet.',
  '',
  'This statement is for project identity verification only. It does not authorize a payment, token transfer, exchange listing, or any financial transaction.'
].join('\n');
const ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
const enc = new TextEncoder();
const $ = id => document.getElementById(id);
let provider = null;
let connected = false;
$('message').textContent = MESSAGE;
function b58(bytes) {
  if (!(bytes instanceof Uint8Array)) throw Error('Invalid bytes');
  let zeroes=0; while(zeroes<bytes.length && bytes[zeroes]===0) zeroes++;
  const digits=[];
  for(let i=zeroes;i<bytes.length;i++){
    let carry=bytes[i];
    for(let j=0;j<digits.length;j++){carry+=digits[j]*256;digits[j]=carry%58;carry=Math.floor(carry/58);}
    while(carry>0){digits.push(carry%58);carry=Math.floor(carry/58);}
  }
  return '1'.repeat(zeroes)+digits.reverse().map(d=>ALPHABET[d]).join('');
}
function un58(value) {
  if(typeof value!=='string' || !value.length) throw Error('Invalid public key');
  let zeroes=0;while(zeroes<value.length && value[zeroes]==='1')zeroes++;
  const out=[];
  for(let i=zeroes;i<value.length;i++){
    let carry=ALPHABET.indexOf(value[i]);if(carry<0)throw Error('Invalid base58');
    for(let j=0;j<out.length;j++){carry+=out[j]*58;out[j]=carry&255;carry>>=8;}
    while(carry>0){out.push(carry&255);carry>>=8;}
  }
  return Uint8Array.from([...new Array(zeroes).fill(0),...out.reverse()]);
}
function status(message){$('status').textContent=message;}
$('connect').addEventListener('click',async()=>{
  try{
    provider=window.phantom?.solana || window.solana;
    if(!provider?.isPhantom || !provider?.connect || !provider?.signMessage)throw Error('Phantom signMessage provider not available. Open in Phantom in-app browser.');
    const result=await provider.connect();
    const address=result?.publicKey?.toString() || provider.publicKey?.toString();
    if(address!==EXPECTED)throw Error('Wrong wallet selected. Expected '+EXPECTED+' but received '+(address||'none'));
    connected=true;$('sign').disabled=false;
    status('Connected to expected wallet: '+address+'. Review the message, then sign.');
  }catch(e){connected=false;$('sign').disabled=true;status('Connection not verified: '+(e?.message||String(e)));}
});
$('sign').addEventListener('click',async()=>{
  $('copy').disabled=true;$('proof').value='';
  try{
    if(!connected||!provider?.isPhantom)throw Error('Connect the correct Phantom wallet first.');
    if(provider.publicKey?.toString()!==EXPECTED)throw Error('Wallet changed; reconnect.');
    if(!crypto?.subtle)throw Error('Secure browser WebCrypto is unavailable.');
    status('Waiting for Phantom message-signing approval…');
    const result=await provider.signMessage(enc.encode(MESSAGE),'utf8');
    const sig=result?.signature;
    if(!sig || !(sig instanceof Uint8Array) || sig.length!==64)throw Error('Phantom returned an invalid Ed25519 signature.');
    const pub=un58(EXPECTED);
    if(pub.length!==32)throw Error('Unexpected public key length.');
    const key=await crypto.subtle.importKey('raw',pub,{name:'Ed25519'},false,['verify']);
    const valid=await crypto.subtle.verify({name:'Ed25519'},key,sig,enc.encode(MESSAGE));
    if(!valid)throw Error('Signature verification failed.');
    const proof={version:1,network:'solana-mainnet',scheme:'ed25519',encoding:'base58',publicKey:EXPECTED,message:MESSAGE,signature:b58(sig),verifiedLocally:true};
    $('proof').value=JSON.stringify(proof,null,2);
    $('copy').disabled=false;status('VERIFIED: message signed by the expected wallet. Copy the proof to share for independent verification.');
  }catch(e){status('NOT VERIFIED: '+(e?.message||String(e)));}
});
$('copy').addEventListener('click',async()=>{
  if($('copy').disabled||!$('proof').value)return;
  try{await navigator.clipboard.writeText($('proof').value);status('Verified proof copied.');}
  catch(e){status('Clipboard unavailable. Select and copy the proof manually.');}
});
