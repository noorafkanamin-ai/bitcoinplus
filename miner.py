import time
import json
import urllib.request
import urllib.parse
import sys
import os
import argparse
import multiprocessing as mp

# Force UTF-8 on Windows terminal
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blockchain.wallet import Wallet
from blockchain.block import Block

def get_block_template(node_url, address):
    try:
        url = f"{node_url}/block/template?address={address}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return None

def submit_block(node_url, block_dict):
    try:
        req = urllib.request.Request(
            f"{node_url}/block/submit",
            data=json.dumps(block_dict).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _worker_process(worker_id, num_workers, index, prev_hash, block_timestamp, transactions, difficulty, stop_event, result_queue, counter):
    """High-Throughput Dual-Engine Mining Worker (Pre-compiled Header Hashing)."""
    import hashlib
    from blockchain.merkle import calculate_merkle_root

    target = "0" * difficulty
    nonce = worker_id
    step = num_workers
    local_count = 0

    # Pre-calculate Merkle root once per block instead of repeating on each nonce
    txids = [t.get("txid") for t in transactions]
    merkle_root = calculate_merkle_root(txids) if txids else ("0" * 64)

    # Base dictionary for canonical JSON
    base_dict = {
        "difficulty": difficulty,
        "index": index,
        "merkle_root": merkle_root,
        "previous_hash": prev_hash,
        "timestamp": block_timestamp
    }

    while not stop_event.is_set():
        base_dict["nonce"] = nonce
        header_str = json.dumps(base_dict, sort_keys=True)
        block_hash = hashlib.sha256(header_str.encode('utf-8')).hexdigest()

        if block_hash.startswith(target):
            stop_event.set()
            solved_block = {
                "index": index,
                "previous_hash": prev_hash,
                "merkle_root": merkle_root,
                "timestamp": block_timestamp,
                "transactions": transactions,
                "nonce": nonce,
                "difficulty": difficulty,
                "hash": block_hash
            }
            result_queue.put(solved_block)
            return

        nonce += step
        local_count += 1
        if local_count >= 10000:
            with counter.get_lock():
                counter.value += local_count
            local_count = 0

DEFAULT_NODE = "https://outtakes-conduit-visibly.ngrok-free.dev"

def mine(node_url=DEFAULT_NODE, address=None, threads=None):
    if not address:
        wallet = Wallet("my_wallet.json")
        address = wallet.address
        print(f"🔑 Using wallet address: {address}")

    num_threads = threads or max(1, os.cpu_count() - 1)

    print("=" * 70)
    print("  ⛏️  Bitcoin Plus (BTCP) Multi-Core CPU Miner")
    print("=" * 70)
    print(f"  🌐 Network Node:    {node_url}")
    print(f"  💰 Payout Address:  {address}")
    print(f"  ⚡ CPU Threads:     {num_threads} Cores Active (Parallel Mining)")
    print("=" * 70)

    total_blocks_mined = 0
    total_rewards = 0.0

    print(f"\n[Connecting] Linking to Bitcoin Plus network at {node_url}...")

    while True:
        template = get_block_template(node_url, address)
        if not template:
            print(f"\r[Waiting] Connecting to node at {node_url}... Retrying in 3s...", end="", flush=True)
            time.sleep(3)
            continue

        index = template["index"]
        prev_hash = template["previous_hash"]
        difficulty = template["difficulty"]
        reward = template["reward"]
        transactions = template["transactions"]

        print(f"\n[⛏️ Mining Block #{index}] Difficulty: {difficulty} zeros | Reward: {reward:.8f} BTCP ({round(reward*100_000_000):,} Satoshis) | Workers: {num_threads}")

        start_time = time.time()
        block_timestamp = time.time()

        stop_event = mp.Event()
        result_queue = mp.Queue()
        counter = mp.Value('i', 0)

        # Launch parallel worker processes
        workers = []
        for i in range(num_threads):
            p = mp.Process(
                target=_worker_process,
                args=(i, num_threads, index, prev_hash, block_timestamp, transactions, difficulty, stop_event, result_queue, counter)
            )
            p.daemon = True
            p.start()
            workers.append(p)

        solved_block = None
        while not stop_event.is_set():
            time.sleep(1.0)
            elapsed = time.time() - start_time
            with counter.get_lock():
                current_count = counter.value
            khs = (current_count / elapsed / 1000) if elapsed > 0 else 0
            print(f"\r  ⚡ Hashing... Total Hashes: {current_count:,} | Combined Speed: {khs:.2f} KH/s", end="", flush=True)

            # Check if template changed on network
            if int(elapsed) % 15 == 0:
                current_template = get_block_template(node_url, address)
                if current_template and current_template["index"] != index:
                    print(f"\n[Notice] Block #{index} already mined by peer! Moving to #{current_template['index']}...")
                    stop_event.set()
                    break

        # Check for result
        if not result_queue.empty():
            solved_block = result_queue.get()

        for p in workers:
            p.join(timeout=0.2)

        if solved_block:
            elapsed = time.time() - start_time
            with counter.get_lock():
                final_hashes = counter.value
            khs = (final_hashes / elapsed / 1000) if elapsed > 0 else 0
            print(f"\n\n🎉 SUCCESS! Block #{index} Mined by your CPU!")
            print(f"   Hash:   {solved_block['hash']}")
            print(f"   Nonce:  {solved_block['nonce']:,} | Time: {elapsed:.2f}s | Speed: {khs:.2f} KH/s")

            res = submit_block(node_url, solved_block)
            if res and res.get("status") == "success":
                total_blocks_mined += 1
                total_rewards += reward
                print(f"   ✅ Block accepted into blockchain!")
                print(f"   🏆 Total Mined: {total_blocks_mined} blocks ({total_rewards:.8f} BTCP | {round(total_rewards * 100_000_000):,} Satoshis)")
            else:
                print(f"   ❌ Block rejected: {res}")
            time.sleep(1)

if __name__ == "__main__":
    mp.freeze_support()  # Required for Windows multiprocessing
    parser = argparse.ArgumentParser(description="Bitcoin Plus Multi-Core CPU Miner")
    parser.add_argument("--node", default=DEFAULT_NODE, help="Node URL")
    parser.add_argument("--address", default=None, help="Your BTCP payout address")
    parser.add_argument("--threads", "-t", type=int, default=None, help="Number of CPU threads to use")
    args = parser.parse_args()

    mine(args.node, args.address, args.threads)
