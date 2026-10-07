# ⚡ Bitcoin Plus (BTCP) - Decentralized CPU-Mineable Cryptocurrency

**Bitcoin Plus (BTCP)** is an independent, fair-launch Proof-of-Work (PoW) cryptocurrency built on pure cryptographic principles (secp256k1 ECDSA, SHA-256 Merkle trees, and Nakamoto consensus). 

Engineered specifically for **CPU mining** with multi-core parallelism and standard **8-decimal Satoshi precision**, Bitcoin Plus allows anyone with a regular computer or a web browser to mine decentralized sound money without expensive ASIC equipment.

---

## 🌟 Key Network Specifications

* **Consensus Mechanism:** Proof-of-Work (PoW) with dynamic difficulty adjustment.
* **Block Reward:** **50.0 BTCP** per block (Classic 2009 Satoshi Model).
* **Maximum Supply:** **21,000,000 BTCP** (Halving every 210,000 blocks).
* **Target Block Time:** 10 minutes (600 seconds).
* **Smallest Unit:** 1 Satoshi Plus (`0.00000001 BTCP`).
* **Cryptography:** secp256k1 ECDSA with BIP-39 12-word mnemonic recovery phrases.
* **Official Pegged OTC Value:** **€520.00 EUR** per 1 BTCP.

---

## ⛏️ How to Mine Bitcoin Plus

You can participate and mine BTCP in two simple ways:

### Option 1: Standalone High-Performance Windows Miner (.exe)
1. Download **`BTCP-Miner.exe`** and **`mine_with_friend.bat`** from this repository.
2. Double-click **`mine_with_friend.bat`**.
3. The miner will automatically connect to the active network node:
   ```bash
   BTCP-Miner.exe --node https://outtakes-conduit-visibly.ngrok-free.dev
   ```
4. The miner will detect all your CPU cores and start hashing in parallel. Rewards are sent directly to your configured wallet!

> **Windows 11 / Smart App Control Note:**  
> If Windows prompts a protection warning for the newly compiled executable:  
> Right-click `BTCP-Miner.exe` &rarr; Click **Properties** &rarr; Check **Unblock** at the bottom &rarr; Click **OK**.

---

### Option 2: Zero-Installation Web Browser Miner
1. Open the official live web portal:  
   👉 **[https://outtakes-conduit-visibly.ngrok-free.dev](https://outtakes-conduit-visibly.ngrok-free.dev)**
2. Scroll to the **⚡ Web Browser Miner** section.
3. Enter your BTCP wallet address (or let the browser auto-generate one for you).
4. Click **▶️ Start Web Mining**.
5. Your browser will start mining using Web Crypto SHA-256. CPU shares and fractional rewards (Satoshis) are credited live on screen!

---

### Option 3: Run via Python (Cross-Platform for Windows / Linux / macOS)
If you have Python 3.10+ installed:
```bash
# 1. Clone the repository
git clone https://github.com/your-username/bitcoin-plus.git
cd bitcoin-plus

# 2. Start mining on your CPU
python miner.py --node https://outtakes-conduit-visibly.ngrok-free.dev
```

---

## 💼 Wallet Management & CLI Tools

Bitcoin Plus includes a full CLI wallet tool with BIP-39 12-word mnemonic recovery:

```bash
# View your address and 12-word seed phrase
python wallet_cli.py info

# Check your confirmed balance
python wallet_cli.py balance

# Restore your wallet from a 12-word backup
python wallet_cli.py restore "your twelve secret recovery seed words here"

# Transfer BTCP to another address
python wallet_cli.py send --to <RECIPIENT_BTCP_ADDRESS> --amount 1.5
```

---

## 💎 Buying BTCP (Official OTC Desk)
BTCP can be acquired directly through the integrated OTC portal on the live web dashboard:
* **Fixed Valuation:** **1 BTCP 
* **Supported Currencies:** Tether (USDT TRC20/ERC20), Bitcoin (BTC), and Ethereum (ETH).
* **Anti-Fraud Security:** Real-time blockchain explorer verification and replay attack protection on all transaction hashes.

---

## 📁 Repository Structure

```text
├── blockchain/              # Core blockchain logic (Consensus, Merkle, ECDSA, Wallet)
│   ├── block.py             # Block header & Merkle root hashing
│   ├── chain.py             # Nakamoto consensus, halving, difficulty, Satoshis
│   ├── transaction.py       # Cryptographic transactions & signatures
│   ├── wallet.py            # secp256k1 key generation & BIP-39 derivation
│   ├── merkle.py            # Binary Merkle tree implementation
│   └── mnemonic.py          # BIP-39 wordlist and PBKDF2 seed generator
├── static/
│   └── index.html           # Live Explorer, Web Miner, OTC Desk & Web Wallet
├── node.py                  # P2P Node, RPC server, Anti-DoS rate limiter
├── miner.py                 # Multi-core CPU parallel mining engine
├── wallet_cli.py            # Command-line wallet manager
├── BTCP-Miner.exe           # Pre-compiled standalone Windows miner
├── mine_with_friend.bat     # 1-Click launcher for friends & public miners
└── README.md                # Documentation and quickstart guide
```

---

## 📜 License
This project is open-source and released under the **MIT License**.
