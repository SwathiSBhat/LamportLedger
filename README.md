# LamportLedger
A distributed blockchain ledger implementation using Lamport's mutual exclusion algorithm, managing client balances and ensuring transaction integrity with transfer and balance operations.

## What does this project do?
This project can run multiple clients where each client has a local copy of a balance table corresponding to each of the clients and a blockchain that has a ledger of the transactions. Each client will also maintain a copy of a banking server that keeps track of every client’s balance in a balance table. A client needs to get mutual exclusion in order to complete transactions to transfer money. The clients use Lamport's mutual exclusion algorithm to perform the transfer operations. 

## Implementation details
1. The Balance Table is a simple Key-Value store, where the key is the client name and the value is the corresponding balance.
2. Each client maintains a Lamport logical clock.
3. Each time a client wants to issue a transfer transaction, it will first exe- cute Lamport’s distributed mutual exclusion protocol. Once it has mutex, the client verifies if it has enough balance to issue this transfer using the local Balance Table. If the client can afford the transfer, then it inserts the transaction block at the head of the blockchain and send that block directly to all other clients, who also insert the block at the head of their local copy of the blockchain. Once inserted in the blockchain, the local copy of the Balance Table is updated. Then mutex is released. If the client does not have enough balance, the transaction is aborted and mutex is released.
4. Once a node is added to a blockchain, the local balance table is updated to reflect the transaction transfer.
5. Each time a client wants to issue a balance transaction, it will check the local copy of the balance and immediately reply with the requesting client’s balance. Mutex is not used in this case.


## How to run?
1. Open 3 terminal instances and start each client using `python3 client.py <clientnum>`
2. The terminal will print the available commands