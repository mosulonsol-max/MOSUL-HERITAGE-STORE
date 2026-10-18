# MOSUL HERITAGE — Whitepaper v0.3

**Public project draft · 18 October 2026**

**Status: A signed wallet statement identifies the mint with the project. Allocation, treasury and payment utility remain unverified or inactive.**

> This paper describes a cultural digital-collectibles project and a proposed future use of MOSUL as a payment option. It is not an offer to buy tokens, investment advice, or a promise of returns, liquidity, listings, sales, or appreciation.

## 1. Project

MOSUL HERITAGE is developing digital collectibles inspired by Mosul’s architecture, places, and cultural history. Each product should publish its classification, source and rights notes, production history, edition, buyer license, and release status before it is offered. An artwork’s cultural inspiration does not by itself make it a verified historical document or grant exclusive rights to the underlying source material.

The project intends to explore MOSUL payments for selected products after product rights are reviewed and a secure checkout and delivery flow passes end-to-end tests. That utility is planned and is not currently active. A separate USDC auction checkout candidate remains disabled and is not MOSUL payment functionality.

## 2. MOSUL mint and smart-contract description

The candidate mint reviewed for this paper is:

`6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump`

Solscan’s mint page, checked on 12 October 2026, displayed the name Mosul (MOSUL), a supply of **1,000,000,000**, **6 decimals**, and the **Token-2022** owner program (`TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`). The explorer displayed **N/A** for mint, freeze, and update authorities. A later Solana RPC snapshot identified the `metadataPointer` and `tokenMetadata` extensions with null metadata update authority, mint authority and freeze authority. These are dated observations; recheck before reliance.

The token is a mint account governed by Solana’s shared Token-2022 program. The Token-2022 program address is not a custom MOSUL program. This repository does not identify a separate MOSUL-specific smart-contract program or publish custom program source code. Accordingly, MOSUL should not be described as having a custom smart contract unless verifiable program evidence is later published.

The mint is an identifier, **not a wallet or merchant payment address**. Do not send funds to it. This paper publishes no payment destination.

## 3. Project binding

The on-chain mint configuration is verifiable independently through the explorer link below. Solscan displays creator `EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu`. On 17 October 2026 that wallet signed a [public statement](MOSUL-WALLET-PROOF-VERIFIED-2026-10-17.json) identifying the exact mint and network as the project's MOSUL token. Its Ed25519 signature was verified independently. This demonstrates control of the signing key and the signer's public declaration.

The signature does not establish the signer's legal identity, ownership of other wallets, the token's original distribution, or exchange approval. No allocation, treasury, lock, burn, or vesting claim is made here without supporting evidence.

## 4. Token facts and open items

| Item | Current record |
| --- | --- |
| Candidate mint | `6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump` |
| Network / owner program | Solana mainnet / Token-2022 |
| Supply shown by explorer | 1,000,000,000 MOSUL |
| Decimals shown by explorer | 6 |
| Mint, freeze, update authorities | Explorer displays N/A for each |
| Token Extensions | RPC snapshot: `metadataPointer` and `tokenMetadata`; null metadata update authority |
| Project statement | Wallet-signed exact mint declaration independently verified 17 October 2026; legal identity outside its scope |
| Allocation / treasury / vesting / burn | Wallet signature published; no verified allocation schedule, treasury designation, vesting or burn claim |
| Checkout / token payment | Inactive; no completed live payment test |
| NFT / product sales | No MOSUL HERITAGE NFT or product is represented here as minted or for sale |

The dated explorer record is a snapshot. Recheck the mint directly before any interaction and do not rely on a token name or symbol to identify a token.

## 5. Proposed utility and product model

A future checkout may allow a buyer to pay for a specific eligible product using MOSUL, subject to transparent pricing, a buyer license, payment confirmation, duplicate-payment rejection, refund handling, and secure delivery. No purchase, ownership of art, NFT, intellectual-property right, governance right, or share of project revenue is granted merely by holding MOSUL.

The first product record must remain blocked until source and rights review, creator and logo authority, authenticity-record validation, buyer-license approval, and payment/delivery checks are complete. A certificate, watermark, or hash can help identify a file; none alone prevents copying or proves a buyer owns an NFT.

## 6. Release gates

1. Completed 17 October 2026: publish and verify the signed project-to-mint statement; preserve its verification record.
2. Publish owner-approved allocation, treasury, and any vesting or lock evidence, or clearly state that no such arrangements exist.
3. Completed in the 17–18 October RPC snapshot: enumerate the observed Token-2022 extensions and preserve the evidence record; refresh it before a listing application.
4. Complete source, rights, logo, and buyer-license review for each product.
5. Test checkout, finality, duplicate-payment protection, refunds, and delivery before enabling sales.
6. If an NFT is planned, publish its standard, metadata, mint transaction, and verifiable asset address only after mint completion.

These are gates, not launch dates. No launch date is promised in this paper.

## 7. Risks

MOSUL can be volatile, illiquid, or lose some or all of its market value. Tokens with similar names or symbols may be unrelated. Wallet mistakes, network or platform outages, integration flaws, and incomplete payment or delivery controls can cause loss. On-chain authority settings do not establish a project’s identity, market integrity, or future behavior. Digital provenance helps verify a specific record but cannot prevent copying. Product licenses, not token ownership alone, define buyer rights.

Nothing here guarantees token value, liquidity, listings, product demand, revenue, NFT issuance, or investment returns. Verify the exact mint, network, and destination before any transfer.

## Sources and verification

- [Solscan: MOSUL mint account](https://solscan.io/token/6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump) — explorer observations checked 12 October 2026.
- [Solana token documentation](https://solana.com/docs/tokens)
- [Solana Token-2022 extensions](https://solana.com/docs/tokens/extensions)
- [On-chain verification record](TOKEN-VERIFICATION.md)
- [Signed project-to-mint statement](MOSUL-WALLET-PROOF-VERIFIED-2026-10-17.json)

## Change log

- **v0.3 — 18 October 2026:** Recorded the verified wallet signature and RPC extension snapshot; clarified that USDC checkout is disabled and MOSUL payment remains planned.
- **v0.2 — 12 October 2026:** Updated token facts from a live Solscan inspection. Explicitly separates verified mint configuration from unverified project binding and proposed utility.
- **v0.1 — 11 October 2026:** Initial public draft.

---

# الورقة البيضاء — MOSUL HERITAGE v0.3

**مسودة مشروع عامة · 18 أكتوبر 2026**

**الحالة: يوجد بيان موقّع من محفظة يعرّف الـMint بعملة المشروع. يظل التوزيع والخزينة ومنفعة الدفع غير متحقق منها أو غير مفعلة.**

> تصف هذه الورقة مشروعًا للمقتنيات الرقمية الثقافية واستخدامًا مستقبليًا مقترحًا لعملة MOSUL كوسيلة دفع. وهي ليست عرضًا لشراء العملة أو نصيحة استثمارية أو وعدًا بالعائد أو السيولة أو الإدراج أو المبيعات أو ارتفاع السعر.

## 1. المشروع

يطوّر MOSUL HERITAGE مقتنيات رقمية مستوحاة من عمارة الموصل وأماكنها وتاريخها الثقافي. ينبغي أن ينشر كل منتج تصنيفه ومصادره وملاحظات الحقوق وسجل الإنتاج والطبعة وترخيص المشتري وحالة الإطلاق قبل عرضه. الاستلهام الثقافي وحده لا يجعل العمل وثيقة تاريخية موثقة ولا يمنح حقوقًا حصرية على المادة المصدرية.

يدرس المشروع إتاحة الدفع بعملة MOSUL لمنتجات مختارة بعد مراجعة حقوق المنتجات واجتياز نظام دفع وتسليم آمن اختبارات كاملة. هذه المنفعة مخطط لها وغير مفعّلة حاليًا. يوجد نموذج أولي منفصل لمزاد ودفع USDC لكنه معطل، ولا يمثل وظيفة للدفع بعملة MOSUL.

## 2. الـMint ووصف العقد الذكي

عنوان الـMint المرشح الذي تمت مراجعته لهذه الورقة:

`6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump`

عرضت صفحة الـMint في Solscan، التي فُحصت في 12 أكتوبر 2026، الاسم Mosul (MOSUL)، ومعروضًا قدره **1,000,000,000**، و**6 منازل عشرية**، وبرنامج **Token-2022** مالكًا للحساب (`TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`). وعرضت N/A لكل من صلاحيات السكّ والتجميد والتحديث. حددت لقطة RPC لاحقة امتدادي `metadataPointer` و`tokenMetadata` مع غياب صلاحيات تحديث البيانات والسكّ والتجميد. هذه ملاحظات مؤرخة يلزم تحديثها قبل الاعتماد عليها.

العملة حساب Mint يديره برنامج Token-2022 المشترك على سولانا. عنوان Token-2022 ليس برنامجًا مخصصًا لـMOSUL. لا يحدد هذا المستودع برنامج عقد ذكي منفصلًا خاصًا بـMOSUL ولا ينشر مصدر برنامج مخصص. لذلك لا ينبغي وصف MOSUL بأنها تملك عقدًا ذكيًا مخصصًا ما لم تُنشر لاحقًا أدلة قابلة للتحقق على وجوده.

عنوان الـMint معرّف للعملة، **وليس محفظة أو عنوان استلام تجاريًا**. لا ترسل أموالًا إليه. ولا تنشر هذه الورقة عنوانًا لاستلام المدفوعات.

## 3. ربط العملة بالمشروع

يمكن التحقق مستقلًا من إعدادات الـMint على الشبكة عبر رابط المستكشف أدناه. تعرض Solscan منشئًا بالعنوان `EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu`. وقّعت هذه المحفظة في 17 أكتوبر 2026 [بيانًا عامًا](MOSUL-WALLET-PROOF-VERIFIED-2026-10-17.json) يحدد الـMint والشبكة وعملة المشروع، وتم التحقق من توقيع Ed25519 استقلاليًا. يثبت ذلك السيطرة على مفتاح التوقيع ونشر تصريح صاحب المحفظة.

لا يثبت التوقيع الهوية القانونية للموقّع، أو ملكية المحافظ الأخرى، أو التوزيع الأصلي للعملة، أو موافقة أي منصة. لا ندعي وجود توزيع أو خزينة أو قفل أو حرق أو استحقاق من دون أدلة مؤيدة.

## 4. حقائق العملة والبنود المفتوحة

| البند | السجل الحالي |
| --- | --- |
| الـMint المرشح | `6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump` |
| الشبكة / البرنامج المالك | Solana mainnet / Token-2022 |
| المعروض الظاهر في المستكشف | 1,000,000,000 MOSUL |
| المنازل العشرية الظاهرة | 6 |
| صلاحيات السكّ والتجميد والتحديث | يعرض المستكشف N/A لكل منها |
| امتدادات Token-2022 | لقطة RPC: `metadataPointer` و`tokenMetadata`؛ صلاحية تحديث البيانات غير موجودة |
| بيان المشروع | تحقق مستقلًا من توقيع المحفظة المحدد للـMint في 17 أكتوبر؛ لا يثبت الهوية القانونية |
| التوزيع والخزينة والاستحقاق والحرق | نُشر توقيع المحفظة؛ ولا يوجد جدول توزيع متحقق أو تحديد مثبت للخزينة أو ادعاء استحقاق أو حرق |
| الدفع بالعملة | غير مفعّل؛ لا يوجد اختبار دفع فعلي مكتمل |
| NFT أو مبيعات منتجات | لا تدعي هذه الورقة إصدار NFT خاصًا بـMOSUL HERITAGE أو وجود منتج معروض للبيع |

سجل المستكشف لقطة مؤرخة. أعد فحص الـMint مباشرة قبل أي تفاعل، ولا تعتمد على الاسم أو الرمز وحدهما لتحديد العملة.

## 5. المنفعة المقترحة ونموذج المنتج

قد يسمح نظام دفع مستقبلي للمشتري بدفع سعر منتج محدد مؤهل باستخدام MOSUL، وفق تسعير واضح وترخيص للمشتري وتأكيد الدفع ورفض الدفعات المكررة ومعالجة الاسترداد والتسليم الآمن. لا يمنح امتلاك MOSUL بحد ذاته شراءً أو ملكيةً للعمل الفني أو NFT أو حقوق ملكية فكرية أو حوكمة أو حصة من إيرادات المشروع.

يجب أن يبقى سجل المنتج الأول محجوبًا حتى اكتمال مراجعة المصدر والحقوق وصلاحية المنشئ والشعار والتحقق من سجل الأصالة واعتماد ترخيص المشتري وفحوص الدفع والتسليم. تساعد الشهادة أو العلامة المائية أو البصمة على تحديد ملف، لكن أيًا منها وحده لا يمنع النسخ أو يثبت أن المشتري يملك NFT.

## 6. بوابات الإطلاق

1. اكتمل في 17 أكتوبر 2026: نشر بيان ارتباط المشروع بالـMint والتحقق من توقيعه وحفظ سجله.
2. نشر التوزيع والخزينة وأدلة الاستحقاق أو القفل المعتمدة من المالك، أو التصريح بوضوح بعدم وجودها.
3. اكتمل في لقطة RPC بتاريخ 17–18 أكتوبر: توثيق الامتدادات المرصودة وحفظ الأدلة؛ تُحدّث قبل طلب الإدراج.
4. إكمال مراجعة المصدر والحقوق والشعار وترخيص المشتري لكل منتج.
5. اختبار الدفع ونهائية المعاملة ومنع الدفع المكرر والاسترداد والتسليم قبل فتح البيع.
6. إذا كان هناك NFT مخطط له، نشر معياره وبياناته الوصفية ومعاملة السكّ وعنوان الأصل القابل للتحقق بعد إتمام السكّ فقط.

هذه بوابات وليست مواعيد. لا تعد هذه الورقة بتاريخ إطلاق.

## 7. المخاطر

قد تتذبذب MOSUL أو تضعف سيولتها أو تفقد جزءًا من قيمتها أو كاملها. قد توجد عملات بأسماء أو رموز مشابهة وغير مرتبطة. يمكن أن تؤدي أخطاء المحفظة أو أعطال الشبكة والمنصة أو عيوب التكامل أو نقص ضوابط الدفع والتسليم إلى خسارة. إعدادات الصلاحيات على الشبكة لا تثبت هوية المشروع أو نزاهة السوق أو السلوك المستقبلي. تساعد سجلات المصدر على التحقق من سجل محدد لكنها لا تمنع النسخ. تحدد تراخيص المنتجات حقوق المشتري؛ أما امتلاك العملة وحده فلا يفعل ذلك.

لا يضمن هذا المحتوى قيمة العملة أو السيولة أو الإدراجات أو الطلب على المنتجات أو الإيرادات أو إصدار NFT أو عوائد الاستثمار. تحقق من الـMint والشبكة والوجهة بدقة قبل أي تحويل.

## المصادر والتحقق

- [Solscan: حساب Mint لعملة MOSUL](https://solscan.io/token/6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump) — ملاحظات المستكشف التي فُحصت في 12 أكتوبر 2026.
- [وثائق رموز سولانا](https://solana.com/docs/tokens)
- [امتدادات Token-2022 في سولانا](https://solana.com/docs/tokens/extensions)
- [سجل التحقق على السلسلة](TOKEN-VERIFICATION.md)
- [البيان الموقّع الذي يحدد الـMint](MOSUL-WALLET-PROOF-VERIFIED-2026-10-17.json)

## سجل التغييرات

- **v0.3 — 18 أكتوبر 2026:** إضافة التوقيع المتحقق منه ولقطة الامتدادات عبر RPC؛ توضيح أن نموذج USDC معطل وأن دفع MOSUL مخطط له.
- **v0.2 — 12 أكتوبر 2026:** تحديث حقائق العملة بعد فحص مباشر لـSolscan، وفصل إعدادات الـMint المتحقق منها عن ربط المشروع والمنفعة المقترحة غير المثبتة.
- **v0.1 — 11 أكتوبر 2026:** المسودة العامة الأولى.
