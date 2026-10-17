import { Connection, Keypair, LAMPORTS_PER_SOL, PublicKey } from '@solana/web3.js';
import bs58 from 'bs58';
import { create, fetchAsset, mplCore, transfer } from '@metaplex-foundation/mpl-core';
import { createUmi } from '@metaplex-foundation/umi-bundle-defaults';
import { generateSigner, keypairIdentity, publicKey } from '@metaplex-foundation/umi';

const RPC = 'https://api.devnet.solana.com';
const METADATA_URI = 'https://example.com/devnet-only-mosul-test.json';

async function main() {
  const connection = new Connection(RPC, 'confirmed');
  const seller = Keypair.generate();
  const recipient = Keypair.generate();
  const umi = createUmi(RPC);
  umi.use(mplCore()).use(keypairIdentity(umi.eddsa.createKeypairFromSecretKey(seller.secretKey)));

  try {
    const signature = await connection.requestAirdrop(seller.publicKey, 50_000_000);
    await connection.confirmTransaction(signature, 'confirmed');

    const asset = generateSigner(umi);
    const created = await create(umi, {
      asset,
      name: 'MOSUL HERITAGE Devnet Transfer Test — Not for Sale',
      uri: METADATA_URI,
    }).sendAndConfirm(umi);

    const afterMint = await fetchAsset(umi, asset.publicKey);
    if (afterMint.owner !== seller.publicKey.toBase58()) {
      throw new Error('minted Core Asset owner did not match the test seller');
    }

    const transferResult = await transfer(umi, {
      asset: asset.publicKey,
      newOwner: publicKey(recipient.publicKey.toBase58()),
    }).sendAndConfirm(umi);
    const afterTransfer = await fetchAsset(umi, asset.publicKey);
    if (afterTransfer.owner !== recipient.publicKey.toBase58()) {
      throw new Error('transferred Core Asset owner did not match the test buyer');
    }

    console.log(JSON.stringify({
      network: 'devnet',
      standard: 'Metaplex Core',
      asset: asset.publicKey,
      originalOwner: seller.publicKey.toBase58(),
      verifiedCurrentOwner: afterTransfer.owner,
      mintSignature: bs58.encode(created.signature),
      transferSignature: bs58.encode(transferResult.signature),
      sellerWallet: seller.publicKey.toBase58(),
      recipientWallet: recipient.publicKey.toBase58(),
      privateKeysPersisted: false,
      metadataUri: METADATA_URI,
      note: 'Disposable Devnet test asset only; not the MOSUL-GENESIS-000001 production NFT.',
      explorer: `https://explorer.solana.com/address/${asset.publicKey}?cluster=devnet`,
    }, null, 2));
  } finally {
    // Key material only existed in process memory.
    seller.secretKey.fill(0);
    recipient.secretKey.fill(0);
  }
}

main().catch((error) => {
  console.error(`Devnet NFT rehearsal failed: ${error?.name ?? 'Error'}: ${error?.message ?? 'unknown error'}`);
  process.exitCode = 1;
});
