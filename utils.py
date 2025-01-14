# Define class for blockchain node
# Each node has the hash of the previous node and a single transaction
# the blockchain is a linked list of nodes

from hashlib import sha256
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns

class Operation:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount

    def __str__(self):
        return f"Sender: {self.sender}, Receiver: {self.receiver}, Amount: {self.amount}"

# To simplify, the blockchain is just a dictionary
# The key is the hash of the operation + incrementing number
# The contents of the block is the operation + the hash of the previous block
class Blockchain:
    def __init__(self):
        self.chain = {}
        self.head = None
        self.block_num = 0

    def add_block(self, operation):
        if self.head is None:
            block_hash = sha256(str(operation).encode() + str(self.block_num).encode()).hexdigest()
            self.chain[block_hash] = (self.block_num, operation, None)
            self.head = block_hash
        else:
            prev_hash = self.head
            block_hash = sha256(str(operation).encode() + str(self.block_num).encode()).hexdigest()
            self.chain[block_hash] = (self.block_num, operation, prev_hash)
            self.head = block_hash
        self.block_num += 1

    def get_block(self, block_hash):
        return self.chain.get(block_hash)

    def get_head(self):
        # Return the contents of the head block
        return self.chain.get(self.head)

    def get_chain(self):
        return self.chain
    
    '''
    Pretty print the blockchain using rich library  
    '''
    def print_blockchain(self):
        console = Console()
        panels = []

        for block_hash, (block_num, operation, prev_hash) in self.chain.items():
            panel_content = (
                f"[b]Block Number:[/b] {block_num}\n"
                f"[b]Operation:[/b] {operation}\n"
                f"[b]Previous Hash:[/b] {prev_hash}\n"
                f"[b]Current Hash:[/b] {block_hash}"
            )
            panels.append(Panel(panel_content, title=f"Block {block_num}", expand=True))

        console.print(Columns(panels))

    def __str__(self):
        return str(self.chain)