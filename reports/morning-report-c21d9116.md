# Morning Compliance Report
**Date:** 2026-05-31 (UTC)
**Classification:** Confidential — Internal Compliance Use Only

---

## 1. Executive Summary

The overnight batch review of 200 transactions identified significant AML and fraud risk exposure, with 81 suspicious transactions, 23 blocked transactions, and an additional transaction requiring immediate human review. A substantial proportion of flagged activity involves payments to defunct or bankrupt crypto entities (BlockFi, Celsius Network, FTX Recovery), high-risk offshore exchanges (Huobi, Gate.io, OKX, Binance), and stablecoin intermediaries (Tether, Paxos), many accompanied by vague memos, off-hours timestamps, and amounts structured near reporting thresholds. Immediate escalation is warranted for the 23 blocked transactions — which collectively represent over **$100 trillion** in flagged value, strongly suggesting a data integrity or system error requiring urgent investigation — as well as for numerous high-risk individual transactions detailed below.

---

## 2. Risk Metrics Overview

### Transaction Counts by Status

| Status | Count |
|---|---|
| Clean | 95 |
| Suspicious | 81 |
| Blocked | 23 |
| Needs Human Review | 1 *(see note)* |
| **Total** | **200** |

> ⚠️ **Note on "Needs Human Review" Count:** The structured metrics report a count of 1 under `needs-human-review`, however the transaction findings contain **multiple dozens** of transactions individually assessed with status `needs-human-review` and recommendation `escalate`. This discrepancy indicates a likely upstream aggregation or pipeline error. **All transactions in Section 3 flagged as `needs-human-review` should be treated as requiring escalation pending resolution of this count mismatch.**

---

### Total Amounts by Status

| Status | Total Amount (Mixed Currencies) |
|---|---|
| Clean | ~232,955 |
| Suspicious | ~2,743,814 |
| Needs Human Review | ~4,500 *(per metrics; actual exposure is materially higher — see note above)* |
| Blocked | ~100,000,003,588,696 |

> 🚨 **CRITICAL DATA INTEGRITY FLAG:** The total blocked amount of approximately **$100 trillion** is clearly anomalous and inconsistent with any plausible transaction portfolio. This figure must be investigated immediately as it likely reflects a system error, data corruption, a test/dummy record injected into production, or a malicious data manipulation attempt. **Do not rely on the blocked-amount figure for any reporting, regulatory filing, or risk assessment until root cause is confirmed.**

---

### Top Suspicious Counterparties (by Occurrence)

| Rank | Counterparty | Suspicious Transaction Count |
|---|---|---|
| 1 | BlockFi | 9 |
| 2 | FTX Recovery | 7 |
| 3 | Huobi | 7 |
| 4 | Tether | 7 |
| 5 | Paxos | 6 |
| 6 | Kraken | 5 |
| 7 | Binance | 4 |
| 8 | Gate.io | 4 |
| 9 | OKX | 3 |
| 10 | Fireblocks | 3 |

> **Note:** BlockFi, FTX Recovery, and Celsius Network are bankrupt/defunct entities. Any transaction directed to these counterparties is presumptively anomalous and requires escalation regardless of amount.

---

## 3. Individual Transaction Findings

---

### TXN-001 — `c16258e3-56ca-4763-a091-39fd2babcceb`
| Field | Detail |
|---|---|
| Amount | $1,000.00 USD |
| Counterparty | Bybit |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** Transaction is future-dated (2026-06-02), directed to Bybit (high-risk cryptocurrency exchange), and carries a vague memo with no discernible business purpose. The combination of future-dating, crypto-exchange counterparty, and insufficient documentation warrants immediate escalation.

---

### TXN-002 — `d63cb615-c32a-4a6a-b21c-f7babb47fe07`
| Field | Detail |
|---|---|
| Amount | £3,534.00 GBP |
| Counterparty | Wise |
| Status | Suspicious |
| Recommendation | Monitor |

**Assessment:** A £3,534 payment to Wise with only "Fee payment" as a memo lacks clear business purpose, invoice reference, or supporting documentation. Pattern is consistent with potential layering or undisclosed third-party fee arrangements.

---

### TXN-003 — `784d1b45-9296-4ac4-898e-7a928768c8ea`
| Field | Detail |
|---|---|
| Amount | £447,500.30 GBP |
| Counterparty | PayPal |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** A £447,500 trade settlement routed through PayPal is highly anomalous. PayPal is a consumer/SME platform unsuitable for large-value trade settlements, which would ordinarily clear via SWIFT, CHAPS, or a regulated correspondent bank. This is a high-priority escalation.

---

### TXN-004 — `b1cfee16-6b0c-48a5-8871-2e4173dc9a40`
| Field | Detail |
|---|---|
| Amount | £4,381.16 GBP |
| Counterparty | FTX Recovery |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** Payment to FTX Recovery — a bankrupt/defunct entity — with a vague "liquidity provision" memo provides no legitimate business justification. Transactions with insolvent counterparties of this profile carry significant fraud and misappropriation risk.

---

### TXN-005 — `9122248d-f3f4-4085-9b86-3f86e95dadf1`
| Field | Detail |
|---|---|
| Amount | €46,291.94 EUR |
| Counterparty | Binance |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** A €46,291.94 payment labeled "monthly subscription fee" routed through Binance is highly implausible. No legitimate subscription service operates at that amount, and routing through a crypto exchange VIP account raises significant structuring and money laundering concerns.

---

### TXN-006 — `897dbf50-20f0-4ce7-84ca-d2b6603a7ffd`
| Field | Detail |
|---|---|
| Amount | $461,455.33 USD |
| Counterparty | KuCoin |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** A $461,455 payment labeled "monthly subscription fee" via KuCoin (a cryptocurrency exchange) is highly anomalous. Legitimate subscription fees do not approach this magnitude, and the use of a crypto exchange introduces significant layering risk consistent with money laundering typologies.

---

### TXN-007 — `1f614917-9930-4681-9031-019658f16a08`
| Field | Detail |
|---|---|
| Amount | €22,789.58 EUR |
| Counterparty | Fireblocks |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** A €22,789 payment described only as "Fee payment" to Fireblocks lacks invoice reference, contractual basis, or cost breakdown. The amount is material and the documentation is insufficient to satisfy AML/KYC standards.

---

### TXN-008 — `4d327a1c-5e45-40b9-afa7-e095451158c7`
| Field | Detail |
|---|---|
| Amount | €29,155.77 EUR |
| Counterparty | Kraken |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** A €29,155 deposit to a Kraken cryptocurrency trading account crosses standard reporting thresholds and lacks documented business justification. Crypto exchange deposits of this magnitude require enhanced due diligence.

---

### TXN-009 — `4ccc33d7-8a0c-42ac-a960-729c4d01005a`
| Field | Detail |
|---|---|
| Amount | $750.50 USD |
| Counterparty | *(None — missing)* |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** This transaction has no counterparty identifier, making recipient verification impossible. The generic memo "Regular payment" provides no additional clarity. Missing counterparty data is a red flag for potential structuring or unauthorized transfer and must be investigated immediately.

---

### TXN-010 — `e45b3a10-7dd2-436a-957b-1efce67270b7`
| Field | Detail |
|---|---|
| Amount | €258,151.89 EUR |
| Counterparty | Bybit |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** A €258,151 transfer labeled "liquidity provision" routed through Bybit (a crypto exchange) is high-risk. The amount is large, the memo is vague, and routing corporate inter-account transfers via a crypto exchange is atypical and consistent with layering.

---

### TXN-011 — `78dbdee2-8959-4671-8a95-e251af790965`
| Field | Detail |
|---|---|
| Amount | $3,119.22 USD |
| Counterparty | Paxos |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** A $3,119.22 transfer via Paxos with no memo provides zero business justification. The amount falls just below common reporting thresholds — a known structuring indicator — and the absence of any documentation compounds the risk.

---

### TXN-012 — `2c06758a-3ad5-43f2-881c-3a8227fdaeb8`
| Field | Detail |
|---|---|
| Amount | $3,619.31 USD |
| Counterparty | FTX Recovery |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** Withdrawal to an external wallet via FTX Recovery, a defunct and bankrupt entity. Transactions with this counterparty present significant fraud, misappropriation, and sanctions-adjacency risk.

---

### TXN-013 — `b1fcb7ce-11d5-495b-9aa3-7f20d918e450`
| Field | Detail |
|---|---|
| Amount | $2,630.22 USD |
| Counterparty | FTX Recovery |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** FTX Recovery counterparty involvement, a 4 AM timestamp, and a generic "payment for services rendered" memo collectively present a high-risk profile consistent with fraud or money laundering. The off-hours processing time is a significant additional red flag.

---

### TXN-014 — `be662973-02f1-4697-83cd-f2235efef21b`
| Field | Detail |
|---|---|
| Amount | $2,452.39 USD |
| Counterparty | BlockFi |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** Transfer to BlockFi — a defunct/bankrupt crypto lender — with no memo. Transacting with an entity no longer operational raises questions about counterparty legitimacy and fund purpose.

---

### TXN-015 — `d3f66048-6ad7-4b4d-819d-8d7edd0c323e`
| Field | Detail |
|---|---|
| Amount | $927.07 USD |
| Counterparty | Revolut |
| Status | Suspicious |
| Recommendation | Monitor |

**Assessment:** A $927.07 Revolut transfer processed at 2:50 AM with no memo. The unusual overnight timing and missing documentation are consistent with structuring or unauthorized fund movement.

---

### TXN-016 — `a4dc6f23-2d46-4261-a13e-76bf5b2d5f07`
| Field | Detail |
|---|---|
| Amount | $68,395.91 USD |
| Counterparty | OKX |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** A $68,395.91 OTC desk settlement via OKX processed at 02:29 UTC is a high-value transaction outside normal business hours through a crypto exchange OTC desk — an elevated money laundering risk combination.

---

### TXN-017 — `74863ea4-4978-4b6c-869a-73f078957921`
| Field | Detail |
|---|---|
| Amount | £36,886.53 GBP |
| Counterparty | Gate.io |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** A £36,886 deposit to a trading account via Gate.io (high-risk crypto exchange) at 01:51 UTC with no supporting documentation. High-value, off-hours, unverified crypto exchange transaction requiring immediate review.

---

### TXN-018 — `b19d0f95-3b86-40b8-9e4a-ef0ebde85d71`
| Field | Detail |
|---|---|
| Amount | £4,262.84 GBP |
| Counterparty | Tether |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** Late-night GBP withdrawal to an external wallet via Tether raises significant layering concerns, particularly given prior notes flagging possible layering between VIP accounts. Off-hours timing and crypto-stablecoin counterparty compound the risk.

---

### TXN-019 — `f9694ff7-2a1a-472f-9700-0e9aaa88a6b6`
| Field | Detail |
|---|---|
| Amount | £285.83 GBP |
| Counterparty | FTX Recovery |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** Transfer through FTX Recovery with no memo. Any transaction involving this defunct counterparty is presumptively high-risk regardless of amount.

---

### TXN-020 — `ac77b413-8ad6-4f40-bfc2-3c94bc82a660`
| Field | Detail |
|---|---|
| Amount | $10,165.24 USD |
| Counterparty | Tether |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** A $10,165.24 transfer via Tether with no memo exceeds the $10,000 CTR threshold and involves a crypto intermediary commonly associated with layering. The absence of any explanatory context materially heightens the risk.

---

### TXN-021 — `427b9920-c0e3-43b8-93d3-adcdd5cce4d6`
| Field | Detail |
|---|---|
| Amount | £2,890.18 GBP |
| Counterparty | Bitfinex |
| Status | Suspicious |
| Recommendation | Monitor |

**Assessment:** A near-£3,000 transfer to Bitfinex with no memo or business justification. Crypto exchange transfers without documented purpose are a common AML concern.

---

### TXN-022 — `30e296ec-9c69-4dff-8c80-376b98e40227`
| Field | Detail |
|---|---|
| Amount | $2,287.75 USD |
| Counterparty | Celsius Network |
| Status | Needs Human Review |
| Recommendation | **Escalate** |

**Assessment:** Transaction involves Celsius Network, a bankrupt and defunct entity. Transacting with an insolvent counterparty may implicate fraudulent transfer rules and creditor claims. Escalation required.

---

### TXN-023 — `b1d3abf8-7b79-406f-b164-745a5c580eec`
| Field | Detail |
|---|---|
| Amount | £