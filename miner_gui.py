import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import urllib.request
import urllib.parse
import os
import sys
import webbrowser

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blockchain.wallet import Wallet
from blockchain.block import Block

def format_amount(val):
    if val is None:
        return "0"
    v = float(val)
    if v == int(v):
        return str(int(v))
    return f"{v:.8f}".rstrip('0').rstrip('.')

DEFAULT_NODE = "https://outtakes-conduit-visibly.ngrok-free.dev"
STATS_FILE = "miner_stats.json"

class BitcoinPlusGUIMiner:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ Bitcoin Plus (BTCP) - Desktop GUI Miner")
        self.root.geometry("700x700")
        self.root.configure(bg="#0a0d16")
        self.root.resizable(False, False)

        self.is_mining = False
        self.mining_thread = None
        self.hashes_count = 0
        self.blocks_mined = 0
        self.shares_accepted = 0
        self.pool_unpaid = 0.0
        self.start_time = 0

        # Load or generate wallet
        self.wallet = Wallet("my_wallet.json")
        self.default_payout = self.wallet.address

        self.setup_ui()
        self.load_local_stats()
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        threading.Thread(target=self.sync_with_node, daemon=True).start()

    def setup_ui(self):
        # Header banner
        header_frame = tk.Frame(self.root, bg="#111827", height=70)
        header_frame.pack(fill="x")

        title_lbl = tk.Label(header_frame, text="⚡ BITCOIN PLUS (BTCP) MINER", font=("Segoe UI", 16, "bold"), fg="#f7931a", bg="#111827")
        title_lbl.pack(pady=(10, 2))

        sub_lbl = tk.Label(header_frame, text="Dual-Engine Proof-of-Work: Solo 50 BTCP Block Mining & Continuous Decimal Pool Shares", font=("Segoe UI", 8), fg="#9ca3af", bg="#111827")
        sub_lbl.pack(pady=(0, 8))

        main_frame = tk.Frame(self.root, bg="#0a0d16", padx=20, pady=10)
        main_frame.pack(fill="both", expand=True)

        # Config Box
        cfg_frame = tk.LabelFrame(main_frame, text=" ⚙️ Mining Configuration ", font=("Segoe UI", 10, "bold"), fg="#38bdf8", bg="#0f172a", bd=1, relief="solid", padx=12, pady=8)
        cfg_frame.pack(fill="x", pady=(0, 10))

        tk.Label(cfg_frame, text="Mining Mode:", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").grid(row=0, column=0, sticky="w", pady=3)
        mode_frame = tk.Frame(cfg_frame, bg="#0f172a")
        mode_frame.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=3)

        self.mode_var = tk.StringVar(value="pool")
        r_pool = tk.Radiobutton(mode_frame, text="⚡ Pool Fractional (Real-Time 0.00005 BTCP / Share)", variable=self.mode_var, value="pool", fg="#10b981", bg="#0f172a", selectcolor="#050811", activebackground="#0f172a", font=("Segoe UI", 9, "bold"), command=self.on_mode_change)
        r_pool.pack(side="left", padx=(0, 12))
        r_solo = tk.Radiobutton(mode_frame, text="🧱 Solo Block (50 BTCP / Full Block)", variable=self.mode_var, value="solo", fg="#f7931a", bg="#0f172a", selectcolor="#050811", activebackground="#0f172a", font=("Segoe UI", 9, "bold"), command=self.on_mode_change)
        r_solo.pack(side="left")

        tk.Label(cfg_frame, text="Network Node URL:", font=("Segoe UI", 9), fg="#94a3b8", bg="#0f172a").grid(row=1, column=0, sticky="w", pady=3)
        self.node_entry = tk.Entry(cfg_frame, font=("Consolas", 9), bg="#050811", fg="#f1f5f9", insertbackground="#fff", bd=1, relief="solid")
        self.node_entry.insert(0, DEFAULT_NODE)
        self.node_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=3)

        tk.Label(cfg_frame, text="Payout Address:", font=("Segoe UI", 9), fg="#94a3b8", bg="#0f172a").grid(row=2, column=0, sticky="w", pady=3)
        self.addr_entry = tk.Entry(cfg_frame, font=("Consolas", 9), bg="#050811", fg="#10b981", insertbackground="#fff", bd=1, relief="solid")
        self.addr_entry.insert(0, self.default_payout)
        self.addr_entry.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=3)
        self.addr_entry.bind("<FocusOut>", lambda e: self.on_address_change())

        tk.Label(cfg_frame, text="CPU Threads:", font=("Segoe UI", 9), fg="#94a3b8", bg="#0f172a").grid(row=3, column=0, sticky="w", pady=3)
        cpu_frame = tk.Frame(cfg_frame, bg="#0f172a")
        cpu_frame.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=3)

        max_cores = max(1, os.cpu_count() or 4)
        self.threads_var = tk.IntVar(value=max(1, max_cores - 1))
        self.threads_spin = tk.Spinbox(cpu_frame, from_=1, to=max_cores, textvariable=self.threads_var, width=5, font=("Consolas", 10), bg="#050811", fg="#fff")
        self.threads_spin.pack(side="left")
        tk.Label(cpu_frame, text=f"(Detected {max_cores} Logical Cores)", font=("Segoe UI", 8), fg="#64748b", bg="#0f172a").pack(side="left", padx=8)

        cfg_frame.columnconfigure(1, weight=1)

        # Performance Stats Grid
        stats_frame = tk.Frame(main_frame, bg="#0a0d16")
        stats_frame.pack(fill="x", pady=(0, 10))

        self.card_speed = self.create_metric_card(stats_frame, "HASHING SPEED", "0.0 KH/s", "#00f2fe", 0)
        self.card_hashes = self.create_metric_card(stats_frame, "TOTAL HASHES", "0", "#f1f5f9", 1)
        self.lbl_progress_title, self.card_progress = self.create_metric_card_with_title(stats_frame, "SHARES ACCEPTED", "0", "#10b981", 2)
        self.lbl_reward_title, self.card_reward = self.create_metric_card_with_title(stats_frame, "POOL REWARD", "0 BTCP", "#f7931a", 3)

        # Action Buttons
        btn_frame = tk.Frame(main_frame, bg="#0a0d16")
        btn_frame.pack(fill="x", pady=(0, 10))

        self.btn_toggle = tk.Button(btn_frame, text="▶️ START MINING", font=("Segoe UI", 11, "bold"), bg="#10b981", fg="#000", activebackground="#059669", activeforeground="#fff", relief="flat", cursor="hand2", command=self.toggle_mining, height=2)
        self.btn_toggle.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_claim = tk.Button(btn_frame, text="💰 CLAIM PAYOUT", font=("Segoe UI", 11, "bold"), bg="#3b82f6", fg="#fff", activebackground="#1d4ed8", activeforeground="#fff", relief="flat", cursor="hand2", command=self.claim_pool_payout, height=2)
        self.btn_claim.pack(side="right", padx=(5, 0))

        # Console Log Window
        log_frame = tk.LabelFrame(main_frame, text=" 📜 Live Mining Telemetry ", font=("Segoe UI", 9, "bold"), fg="#94a3b8", bg="#0a0d16", bd=1, relief="solid")
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_frame, bg="#03050a", fg="#94a3b8", font=("Consolas", 8), relief="flat", wrap="word", height=7)
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)

        # Footer links
        footer = tk.Frame(self.root, bg="#0a0d16", padx=20, pady=6)
        footer.pack(fill="x")
        
        btn_dash = tk.Button(footer, text="🌐 Open Web Wallet & Bridge", font=("Segoe UI", 8), bg="#1e293b", fg="#38bdf8", relief="flat", cursor="hand2", command=lambda: webbrowser.open(DEFAULT_NODE + "/wallet"))
        btn_dash.pack(side="left")

        self.status_lbl = tk.Label(footer, text="⚡ Mode: Fractional Pool Shares | 1 BTCP = €520.00 EUR", font=("Segoe UI", 8), fg="#64748b", bg="#0a0d16")
        self.status_lbl.pack(side="right")

    def create_metric_card(self, parent, label, default_val, val_color, col_idx):
        _, val_lbl = self.create_metric_card_with_title(parent, label, default_val, val_color, col_idx)
        return val_lbl

    def create_metric_card_with_title(self, parent, label, default_val, val_color, col_idx):
        card = tk.Frame(parent, bg="#0f172a", bd=1, relief="solid", padx=8, pady=8)
        card.grid(row=0, column=col_idx, sticky="nsew", padx=3)
        parent.columnconfigure(col_idx, weight=1)

        t_lbl = tk.Label(card, text=label, font=("Segoe UI", 7, "bold"), fg="#64748b", bg="#0f172a")
        t_lbl.pack(anchor="w")
        val_lbl = tk.Label(card, text=default_val, font=("Consolas", 11, "bold"), fg=val_color, bg="#0f172a")
        val_lbl.pack(anchor="w", pady=(3, 0))
        return t_lbl, val_lbl

    def load_local_stats(self):
        payout = self.addr_entry.get().strip() if hasattr(self, 'addr_entry') else self.default_payout
        if not payout:
            return
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    all_stats = json.load(f)
                    stats = all_stats.get(payout, {})
                    self.shares_accepted = stats.get("shares_accepted", self.shares_accepted)
                    self.pool_unpaid = float(stats.get("pool_unpaid", self.pool_unpaid))
                    self.blocks_mined = stats.get("blocks_mined", self.blocks_mined)
                    self.hashes_count = stats.get("total_hashes", self.hashes_count)
                    self.update_stats_display()
            except Exception:
                pass

    def save_local_stats(self):
        payout = self.addr_entry.get().strip() if hasattr(self, 'addr_entry') else self.default_payout
        if not payout:
            return
        all_stats = {}
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    all_stats = json.load(f)
            except Exception:
                all_stats = {}
        all_stats[payout] = {
            "shares_accepted": self.shares_accepted,
            "pool_unpaid": self.pool_unpaid,
            "blocks_mined": self.blocks_mined,
            "total_hashes": self.hashes_count,
            "last_updated": time.time()
        }
        try:
            temp_f = STATS_FILE + ".tmp"
            with open(temp_f, "w", encoding="utf-8") as f:
                json.dump(all_stats, f, indent=2)
            os.replace(temp_f, STATS_FILE)
        except Exception:
            pass

    def sync_with_node(self):
        try:
            node_url = self.node_entry.get().strip().rstrip("/") if hasattr(self, 'node_entry') else DEFAULT_NODE
            payout = self.addr_entry.get().strip() if hasattr(self, 'addr_entry') else self.default_payout
            if not payout:
                return
            url = f"{node_url}/pool/miner?address={urllib.parse.quote(payout)}"
            req = urllib.request.Request(url, headers={"User-Agent": "BTCP-GUI-Miner/2.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                remote_unpaid = float(data.get("unpaid_reward", 0.0))
                remote_shares = int(data.get("shares", 0))
                if remote_unpaid > self.pool_unpaid or remote_shares > self.shares_accepted:
                    self.pool_unpaid = max(self.pool_unpaid, remote_unpaid)
                    self.shares_accepted = max(self.shares_accepted, remote_shares)
                    self.update_stats_display()
                    self.save_local_stats()
                    self.log(f"🔄 Restored session from pool: {format_amount(self.pool_unpaid)} BTCP ({self.shares_accepted} shares)")
        except Exception:
            pass

    def on_address_change(self):
        self.load_local_stats()
        threading.Thread(target=self.sync_with_node, daemon=True).start()

    def update_stats_display(self):
        try:
            mode = self.mode_var.get()
            if mode == "pool":
                self.lbl_progress_title.configure(text="SHARES ACCEPTED")
                self.card_progress.configure(text=str(self.shares_accepted))
                self.lbl_reward_title.configure(text="POOL REWARD")
                self.card_reward.configure(text=f"{format_amount(self.pool_unpaid)} BTCP")
            else:
                self.lbl_progress_title.configure(text="BLOCKS MINED")
                self.card_progress.configure(text=str(self.blocks_mined))
                self.lbl_reward_title.configure(text="EARNED REWARD")
                self.card_reward.configure(text=f"{format_amount(self.blocks_mined * 50)} BTCP")
            self.card_hashes.configure(text=f"{self.hashes_count:,}")
        except Exception:
            pass

    def on_mode_change(self):
        mode = self.mode_var.get()
        if mode == "pool":
            self.lbl_progress_title.configure(text="SHARES ACCEPTED")
            self.card_progress.configure(text=str(self.shares_accepted))
            self.lbl_reward_title.configure(text="POOL REWARD")
            self.card_reward.configure(text=f"{format_amount(self.pool_unpaid)} BTCP")
            self.status_lbl.configure(text="⚡ Mode: Fractional Pool Shares | 1 BTCP = €520.00 EUR")
            self.btn_claim.configure(state="normal")
        else:
            self.lbl_progress_title.configure(text="BLOCKS MINED")
            self.card_progress.configure(text=str(self.blocks_mined))
            self.lbl_reward_title.configure(text="EARNED REWARD")
            self.card_reward.configure(text=f"{format_amount(self.blocks_mined * 50)} BTCP")
            self.status_lbl.configure(text="🧱 Mode: Solo Block Mining (50 BTCP per block)")
            self.btn_claim.configure(state="disabled")

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def claim_pool_payout(self):
        node_url = self.node_entry.get().strip().rstrip("/")
        payout = self.addr_entry.get().strip()
        if not payout:
            messagebox.showerror("Error", "Payout address required.")
            return

        def do_payout():
            try:
                self.log(f"💸 Requesting payout for {payout}...")
                req = urllib.request.Request(
                    f"{node_url}/pool/payout",
                    data=json.dumps({"address": payout}).encode('utf-8'),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    res = json.loads(resp.read().decode('utf-8'))
                    if res.get("status") == "success":
                        amt = res.get("amount", 0.0)
                        txid = res.get("txid", "")
                        self.pool_unpaid = 0.0
                        self.save_local_stats()
                        self.card_reward.configure(text="0 BTCP")
                        self.log(f"🎉 PAYOUT SUCCESSFUL! {format_amount(amt)} BTCP transferred to your on-chain wallet!")
                        self.log(f"🔗 Blockchain TXID: {txid}")
                        messagebox.showinfo("Payout Complete", f"Successfully paid out {format_amount(amt)} BTCP to your wallet!\n\nTXID: {txid}")
                    else:
                        self.log(f"⚠️ Payout failed: {res.get('message')}")
                        messagebox.showwarning("Payout Notice", res.get("message"))
            except Exception as e:
                self.log(f"❌ Payout error: {e}")
                messagebox.showerror("Error", str(e))

        threading.Thread(target=do_payout, daemon=True).start()

    def on_window_close(self):
        self.is_mining = False
        self.save_local_stats()
        self.root.destroy()

    def toggle_mining(self):
        if self.is_mining:
            self.is_mining = False
            self.save_local_stats()
            self.btn_toggle.configure(text="▶️ START MINING", bg="#10b981")
            self.log("⏹️ Mining stopped by user.")
        else:
            node_url = self.node_entry.get().strip().rstrip("/")
            payout = self.addr_entry.get().strip()
            if not payout:
                messagebox.showerror("Error", "Payout address cannot be empty!")
                return

            self.is_mining = True
            self.btn_toggle.configure(text="⏹️ STOP MINING", bg="#ef4444")
            self.start_time = time.time()
            mode = self.mode_var.get()
            self.log(f"🚀 Initializing multi-core CPU miner connected to {node_url} (Mode: {mode.upper()})...")
            self.mining_thread = threading.Thread(target=self.mining_worker, args=(node_url, payout, mode), daemon=True)
            self.mining_thread.start()

    def mining_worker(self, node_url, payout, mode):
        while self.is_mining:
            try:
                url = f"{node_url}/block/template?address={payout}"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    template = json.loads(resp.read().decode('utf-8'))
            except Exception as e:
                self.log(f"⚠️ Connecting to node... Retrying ({e})")
                time.sleep(3)
                continue

            index = template["index"]
            prev_hash = template["previous_hash"]
            block_difficulty = template["difficulty"]
            reward = template["reward"]
            transactions = template["transactions"]
            block_target = "0" * block_difficulty
            share_target = "000"  # 3 zeros for fractional pool share
            block_ts = time.time()

            if mode == "solo":
                self.log(f"⛏️ Solo Mining Block #{index} (Difficulty: {block_difficulty} zeros | Reward: {format_amount(reward)} BTCP)")
            else:
                self.log(f"⚡ Pool Mining (Share Difficulty: 3 zeros | Reward: 0.00005 BTCP / share)")

            nonce = int(time.time() * 1000) % 5000000
            solved_block = None

            while self.is_mining:
                for _ in range(1200):
                    nonce += 1
                    self.hashes_count += 1
                    block = Block(index, prev_hash, block_ts, transactions, nonce, block_difficulty)
                    
                    if mode == "pool" and block.hash.startswith(share_target):
                        # Pool share found!
                        try:
                            s_req = urllib.request.Request(
                                f"{node_url}/pool/share",
                                data=json.dumps({"address": payout, "hash": block.hash, "hashes": 1200}).encode('utf-8'),
                                headers={"Content-Type": "application/json"}
                            )
                            with urllib.request.urlopen(s_req, timeout=4) as s_resp:
                                res = json.loads(s_resp.read().decode('utf-8'))
                                if res.get("status") == "accepted":
                                    self.shares_accepted += 1
                                    self.pool_unpaid = res.get("unpaid_float", self.pool_unpaid + 0.00005)
                                    self.save_local_stats()
                                    self.card_progress.configure(text=str(self.shares_accepted))
                                    self.card_reward.configure(text=f"{format_amount(self.pool_unpaid)} BTCP")
                                    self.log(f"✅ Share accepted! +0.00005 BTCP | Pool Bal: {format_amount(self.pool_unpaid)} BTCP")
                        except Exception:
                            pass

                    if block.hash.startswith(block_target):
                        solved_block = block
                        break

                elapsed = time.time() - self.start_time
                speed = (self.hashes_count / elapsed / 1000) if elapsed > 0 else 0
                self.card_speed.configure(text=f"{speed:.2f} KH/s")
                self.card_hashes.configure(text=f"{self.hashes_count:,}")

                if solved_block:
                    self.log(f"🎉 FULL BLOCK #{index} MINED! Nonce: {nonce:,} | Hash: {solved_block.hash[:16]}...")
                    try:
                        submit_req = urllib.request.Request(
                            f"{node_url}/block/submit",
                            data=json.dumps(solved_block.to_dict()).encode('utf-8'),
                            headers={"Content-Type": "application/json"}
                        )
                        with urllib.request.urlopen(submit_req, timeout=5) as s_resp:
                            res = json.loads(s_resp.read().decode('utf-8'))
                            if res.get("status") == "success":
                                self.blocks_mined += 1
                                self.save_local_stats()
                                if mode == "solo":
                                    self.card_progress.configure(text=str(self.blocks_mined))
                                    self.card_reward.configure(text=f"{format_amount(self.blocks_mined * 50)} BTCP")
                                self.log(f"✅ Block accepted into chain! +50 BTCP credited to your wallet.")
                    except Exception as e:
                        self.log(f"❌ Submission failed: {e}")
                    break

def main():
    root = tk.Tk()
    app = BitcoinPlusGUIMiner(root)
    root.mainloop()

if __name__ == "__main__":
    main()
