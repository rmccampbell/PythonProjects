class Node:
    def __init__(self, data=0, next=None):
        self.data = data
        self.next = next

    def __repr__(self):
        return 'Node(%r)' % self.data

class LinkedList:
    def __init__(self, iter=()):
        self.next = None
        node = self
        for o in iter:
            node.next = node = Node(o)

    @property
    def head(self):
        return self.next

    def __bool__(self):
        return self.next is not None

    def __repr__(self):
        return 'LinkedList([%s])' % ', '.join(map(repr, self))

    def __len__(self):
        n = 0
        node = self.next
        while node:
            n += 1
            node = node.next
        return n

    def __iter__(self):
        node = self.next
        while node:
            yield node.data
            node = node.next

    def nodes(self):
        node = self.next
        while node:
            yield node
            node = node.next

    def tail(self):
        node = self
        while node.next:
            node = node.next
        return node

    def insert(self, value, node=None):
        node = node or self
        node.next = Node(value, node.next)
        return node.next

    def remove(self, node=None):
        node = node or self
        if not node.next:
            raise ValueError("can't remove past last node")
        node.next = node.next.next

    def insert_all(self, values, node=None):
        node = node or self
        for value in values:
            node = self.insert(value, node)
        return node if node is not self else None

    def remove_all(self, node1=None, node2=None):
        node1 = node1 or self
        while node1.next != node2:
            self.remove(node1)

    def find(self, value):
        node = self.next
        while node:
            if node.data == value:
                return node
            node = node.next
        return node

    def find_prev(self, value):
        node = self
        while node.next:
            if node.next.data == value:
                return node
            node = node.next
        return node if node is not self else None

    def reverse(self):
        prev = None
        node = self.next
        while node:
            next = node.next
            node.next = prev
            prev = node
            node = next
        self.next = prev
        return self


def merge(l1, l2):
    l3 = LinkedList()
    n1 = l1.next
    n2 = l2.next
    n3 = None
    while n1 or n2:
        if n1 and (not n2 or n1.data <= n2.data):
            val = n1.data
            n1 = n1.next
        else:
            val = n2.data
            n2 = n2.next
        n3 = l3.insert(val, n3)
    return l3


def add(l1, l2):
    l3 = LinkedList()
    n1 = l1.next
    n2 = l2.next
    n3 = None
    c = 0
    last = None
    while n1 or n2:
        x1 = n1.data if n1 else 0
        x2 = n2.data if n2 else 0
        c, s = divmod(x1 + x2 + c, 10)
        n3 = l3.insert(s, n3)
        if s:
            last = n3
        n1 = n1 and n1.next
        n2 = n2 and n2.next
    if c:
        l3.insert(c, n3)
    else:
        l3.remove_all(last)
    return l3

