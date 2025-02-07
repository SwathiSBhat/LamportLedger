# LamportLedger
This project implements a distributed blockchain ledger using Lamport’s mutual exclusion algorithm to manage client balances and ensure transaction integrity through transfer and balance operations.

## Functionality
- Each client maintains a local balance table and a blockchain ledger recording all transactions.
- Clients also run a banking server that tracks all balances.
- To perform a transfer, a client acquires mutual exclusion using Lamport’s algorithm, verifies its balance, and updates the blockchain upon successful transfer.
- Transactions propagate to all clients, ensuring consistency across the distributed system.
- Balance inquiries are handled instantly using the local balance table without requiring mutual exclusion.

## Implementation Details
- The Balance Table is a key-value store mapping client names to balances.
- Each client maintains a Lamport logical clock for ordering events.
- For transfer transactions:
  - The client executes Lamport’s mutual exclusion protocol.
  - If sufficient funds exist, the transaction is recorded in the blockchain and broadcast to all clients.
  - Each client updates its local balance table accordingly.
  - If insufficient funds exist, the transaction is aborted, and mutex is released.
- Balance queries directly read the local balance table without requiring mutex.

## How to Run
1. Open three terminal instances.
2. Start each client using:
```
python3 client.py <clientnum>
```
3. The terminal will display available commands.
