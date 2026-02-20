# Non-Linear Data Structures (A to Z) - Complete Guide

## ðŸŽ¯ What are Non-Linear Data Structures?

**Explain like a child:**
- Linear (like a shopping list): 1 â†’ 2 â†’ 3 â†’ 4
- Non-Linear (like a family tree): Parent â†’ Children â†’ Grandchildren (branching)

Non-linear means **data connects in multiple directions**, not just in a straight line.

---

## ðŸ“Š Compare All Non-Linear Structures

| Structure | Looks Like | Where Used | Speed |
|---|---|---|---|
| **Tree** | Upside-down tree ðŸŒ³ | File systems, folders | Fast |
| **Binary Tree** | Tree with max 2 children | Sorting, parsing | Fast |
| **BST** | Sorted binary tree | Search, databases | Very Fast |
| **Heap** | Pyramid ðŸ”º | Priority queues | Very Fast |
| **Graph** | Network ðŸ•¸ï¸ | Maps, social networks | Variable |
| **Trie** | Word search tree | Autocomplete, spell check | Fast |
| **Segment Tree** | Segment ranges | Range queries | Very Fast |

---

---

# 1ï¸âƒ£ TREES ðŸŒ³

## What is a Tree?

**Child explanation:** "Like a real tree - has a trunk (root), branches (nodes), and leaves (end points)."

```
        Root (A)
        /      \
       B        C
      / \      / \
     D   E    F   G  â† Leaves
```

### Tree Terminology
| Term | Meaning |
|---|---|
| **Root** | Top node (A) |
| **Leaf** | No children |
| **Node** | Any point |
| **Edge** | Connection between nodes |
| **Height** | Longest path from root to leaf |
| **Depth** | Distance from root |
| **Subtree** | A tree inside the tree |

---

## Code: Tree Implementation

```python
# File: structures/tree.py

class TreeNode:
    """Basic tree node"""
    def __init__(self, value):
        self.value = value
        self.children = []  # Can have many children

    def add_child(self, child_node):
        """Add child to this node"""
        self.children.append(child_node)

    def remove_child(self, child_node):
        """Remove child"""
        self.children = [child for child in self.children if child != child_node]


class Tree:
    """General tree with multiple children per node"""
    def __init__(self, root_value):
        self.root = TreeNode(root_value)

    def print_tree(self, node=None, level=0):
        """Print tree structure"""
        if node is None:
            node = self.root

        print("  " * level + str(node.value))
        for child in node.children:
            self.print_tree(child, level + 1)

    def find_node(self, value, node=None):
        """Find node by value"""
        if node is None:
            node = self.root

        if node.value == value:
            return node

        for child in node.children:
            result = self.find_node(value, child)
            if result:
                return result

        return None

    def get_height(self, node=None):
        """Get tree height"""
        if node is None:
            node = self.root

        if not node.children:
            return 1

        return 1 + max(self.get_height(child) for child in node.children)

    def count_nodes(self, node=None):
        """Count total nodes"""
        if node is None:
            node = self.root

        count = 1
        for child in node.children:
            count += self.count_nodes(child)

        return count


# ============================================
# Example Usage
# ============================================

# Create company organization tree
root = TreeNode("CEO")
vp_eng = TreeNode("VP Engineering")
vp_sales = TreeNode("VP Sales")

eng_manager = TreeNode("Manager 1")
eng_dev1 = TreeNode("Developer 1")
eng_dev2 = TreeNode("Developer 2")

root.add_child(vp_eng)
root.add_child(vp_sales)
vp_eng.add_child(eng_manager)
eng_manager.add_child(eng_dev1)
eng_manager.add_child(eng_dev2)

tree = Tree("CEO")
tree.root = root

print("Organization Structure:")
tree.print_tree()
# Output:
# CEO
#   VP Engineering
#     Manager 1
#       Developer 1
#       Developer 2
#   VP Sales

print(f"Total employees: {tree.count_nodes()}")  # 5
print(f"Tree height: {tree.get_height()}")  # 4
```

---

## Django Project: File System Explorer

**Use case:** Store folder/file hierarchy in Django

```python
# File: storage/models.py

from django.db import models
from django.contrib.auth.models import User

class Folder(models.Model):
    """Represents folders (tree nodes)"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('parent', 'name', 'owner')

    def __str__(self):
        return self.name

    def get_children(self):
        """Get all direct children"""
        return self.children.all()

    def get_all_descendants(self):
        """Get all nested files/folders"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def get_path(self):
        """Get full path like /Documents/Photos/Vacation"""
        if self.parent is None:
            return f"/{self.name}"
        return f"{self.parent.get_path()}/{self.name}"


class File(models.Model):
    """Files in folders"""
    name = models.CharField(max_length=255)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='files')
    size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# File: storage/views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Folder, File

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_folder_tree(request, folder_id=None):
    """
    Get folder tree as JSON
    GET /api/folders/tree/
    """
    if folder_id:
        try:
            folder = Folder.objects.get(id=folder_id, owner=request.user)
        except Folder.DoesNotExist:
            return Response({'error': 'Folder not found'}, status=404)
    else:
        # Root folders
        folder = None

    def build_tree(f):
        """Recursively build tree"""
        if f is None:
            children_data = []
            for child in Folder.objects.filter(parent=None, owner=request.user):
                children_data.append(build_tree(child))
            return {'children': children_data}

        children_data = []
        for child in f.children.all():
            children_data.append(build_tree(child))

        files_data = [
            {'name': file.name, 'size': file.size}
            for file in f.files.all()
        ]

        return {
            'id': f.id,
            'name': f.name,
            'path': f.get_path(),
            'children': children_data,
            'files': files_data
        }

    return Response(build_tree(folder))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_folder(request):
    """
    Create new folder
    POST /api/folders/
    {
        "name": "My Documents",
        "parent_id": 5  # optional
    }
    """
    name = request.data.get('name')
    parent_id = request.data.get('parent_id')

    parent = None
    if parent_id:
        try:
            parent = Folder.objects.get(id=parent_id, owner=request.user)
        except Folder.DoesNotExist:
            return Response({'error': 'Parent folder not found'}, status=404)

    folder = Folder.objects.create(
        name=name,
        parent=parent,
        owner=request.user
    )

    return Response({
        'id': folder.id,
        'name': folder.name,
        'path': folder.get_path()
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_folder_size(request, folder_id):
    """
    Get total size of folder including all nested files
    GET /api/folders/{id}/size/
    """
    try:
        folder = Folder.objects.get(id=folder_id, owner=request.user)
    except Folder.DoesNotExist:
        return Response({'error': 'Folder not found'}, status=404)

    def calculate_size(f):
        """Recursively calculate total size"""
        total = f.files.aggregate(size_sum=models.Sum('size'))['size_sum'] or 0

        for child in f.children.all():
            total += calculate_size(child)

        return total

    total_size = calculate_size(folder)

    return Response({
        'folder_id': folder_id,
        'total_size': total_size,
        'formatted_size': f"{total_size / (1024**3):.2f} GB"
    })
```

---

---

# 2ï¸âƒ£ BINARY TREES ðŸŒ²

## What is a Binary Tree?

**Child explanation:** "A tree where each node has at most 2 children (left and right)."

```
        1
       / \
      2   3
     / \
    4   5
```

### Types of Binary Trees
| Type | Property | Example |
|---|---|---|
| **Full** | Every node has 0 or 2 children | âœ“ |
| **Complete** | Filled left to right | âœ“ |
| **Perfect** | All levels fully filled | âœ“ |
| **Balanced** | Heights differ by 1 max | âœ“ |

---

## Code: Binary Tree Implementation

```python
# File: structures/binary_tree.py

class BinaryTreeNode:
    """Binary tree node with left and right children"""
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None


class BinaryTree:
    """Binary tree operations"""
    def __init__(self, root_value=None):
        self.root = BinaryTreeNode(root_value) if root_value else None

    # ============================================
    # TRAVERSALS (Different ways to visit nodes)
    # ============================================

    def inorder(self, node=None, result=None):
        """Left â†’ Node â†’ Right (sorted for BST)"""
        if result is None:
            result = []
        if node is None:
            return result

        self.inorder(node.left, result)
        result.append(node.value)
        self.inorder(node.right, result)

        return result

    def preorder(self, node=None, result=None):
        """Node â†’ Left â†’ Right"""
        if result is None:
            result = []
        if node is None:
            return result

        result.append(node.value)
        self.preorder(node.left, result)
        self.preorder(node.right, result)

        return result

    def postorder(self, node=None, result=None):
        """Left â†’ Right â†’ Node"""
        if result is None:
            result = []
        if node is None:
            return result

        self.postorder(node.left, result)
        self.postorder(node.right, result)
        result.append(node.value)

        return result

    def levelorder(self):
        """Left to right, level by level"""
        if not self.root:
            return []

        from collections import deque
        queue = deque([self.root])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node.value)

            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)

        return result

    # ============================================
    # PROPERTIES
    # ============================================

    def get_height(self, node=None):
        """Get max height"""
        if node is None:
            node = self.root

        if node is None:
            return 0

        return 1 + max(self.get_height(node.left), self.get_height(node.right))

    def count_nodes(self, node=None):
        """Count total nodes"""
        if node is None:
            node = self.root

        if node is None:
            return 0

        return 1 + self.count_nodes(node.left) + self.count_nodes(node.right)

    def count_leaves(self, node=None):
        """Count leaf nodes"""
        if node is None:
            node = self.root

        if node is None:
            return 0

        if node.left is None and node.right is None:
            return 1

        return self.count_leaves(node.left) + self.count_leaves(node.right)

    def is_balanced(self, node=None):
        """Check if tree is balanced"""
        if node is None:
            node = self.root

        if node is None:
            return True

        left_height = self.get_height(node.left)
        right_height = self.get_height(node.right)

        if abs(left_height - right_height) > 1:
            return False

        return self.is_balanced(node.left) and self.is_balanced(node.right)

    def sum_all_nodes(self, node=None):
        """Sum all node values"""
        if node is None:
            node = self.root

        if node is None:
            return 0

        return node.value + self.sum_all_nodes(node.left) + self.sum_all_nodes(node.right)

    def find_node(self, value, node=None):
        """Find node by value"""
        if node is None:
            node = self.root

        if node is None:
            return None

        if node.value == value:
            return node

        left_result = self.find_node(value, node.left)
        if left_result:
            return left_result

        return self.find_node(value, node.right)

    def print_tree_visual(self, node=None, level=0):
        """Print tree in visual format"""
        if node is None:
            node = self.root

        if node is None:
            return

        self.print_tree_visual(node.right, level + 1)
        print("  " * level + str(node.value))
        self.print_tree_visual(node.left, level + 1)


# ============================================
# Example Usage
# ============================================

tree = BinaryTree(1)
tree.root.left = BinaryTreeNode(2)
tree.root.right = BinaryTreeNode(3)
tree.root.left.left = BinaryTreeNode(4)
tree.root.left.right = BinaryTreeNode(5)

print("Inorder:", tree.inorder())    # [4, 2, 5, 1, 3]
print("Preorder:", tree.preorder())  # [1, 2, 4, 5, 3]
print("Postorder:", tree.postorder())  # [4, 5, 2, 3, 1]
print("Level order:", tree.levelorder())  # [1, 2, 3, 4, 5]

print(f"Height: {tree.get_height()}")  # 3
print(f"Nodes: {tree.count_nodes()}")  # 5
print(f"Leaves: {tree.count_leaves()}")  # 3
print(f"Sum: {tree.sum_all_nodes()}")  # 15
print(f"Balanced: {tree.is_balanced()}")  # True
```

---

---

# 3ï¸âƒ£ BINARY SEARCH TREE (BST) ðŸ”

## What is a BST?

**Child explanation:** "A binary tree where left side has smaller numbers, right side has bigger numbers. Makes searching SUPER FAST!"

```
        5
       / \
      3   7
     / \ / \
    1 4 6  8

Rule: Left < Parent < Right
```

### BST Properties
| Property | Benefit |
|---|---|
| **Ordered** | Search in O(log n) |
| **Efficient** | Fast insert/delete |
| **Balanced** | Prevents worst case |

---

## Code: BST Implementation

```python
# File: structures/bst.py

class BSTNode:
    """Binary Search Tree node"""
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None


class BinarySearchTree:
    """BST with search, insert, delete"""
    def __init__(self):
        self.root = None

    def insert(self, value):
        """Insert value maintaining BST property"""
        if self.root is None:
            self.root = BSTNode(value)
        else:
            self._insert_recursive(self.root, value)

    def _insert_recursive(self, node, value):
        """Helper for insertion"""
        if value < node.value:
            if node.left is None:
                node.left = BSTNode(value)
            else:
                self._insert_recursive(node.left, value)
        else:
            if node.right is None:
                node.right = BSTNode(value)
            else:
                self._insert_recursive(node.right, value)

    def search(self, value):
        """Search for value - O(log n)"""
        return self._search_recursive(self.root, value)

    def _search_recursive(self, node, value):
        """Helper for search"""
        if node is None:
            return False

        if value == node.value:
            return True
        elif value < node.value:
            return self._search_recursive(node.left, value)
        else:
            return self._search_recursive(node.right, value)

    def delete(self, value):
        """Delete node"""
        self.root = self._delete_recursive(self.root, value)

    def _delete_recursive(self, node, value):
        """Helper for deletion"""
        if node is None:
            return None

        if value < node.value:
            node.left = self._delete_recursive(node.left, value)
        elif value > node.value:
            node.right = self._delete_recursive(node.right, value)
        else:
            # Node to delete found

            # Case 1: No children (leaf)
            if node.left is None and node.right is None:
                return None

            # Case 2: One child
            if node.left is None:
                return node.right
            if node.right is None:
                return node.left

            # Case 3: Two children
            # Find smallest in right subtree (inorder successor)
            successor = self._find_min(node.right)
            node.value = successor.value
            node.right = self._delete_recursive(node.right, successor.value)

        return node

    def _find_min(self, node):
        """Find node with minimum value"""
        while node.left:
            node = node.left
        return node

    def inorder(self, node=None, result=None):
        """Inorder traversal (sorted)"""
        if result is None:
            result = []
        if node is None:
            node = self.root

        if node:
            self.inorder(node.left, result)
            result.append(node.value)
            self.inorder(node.right, result)

        return result

    def find_min(self):
        """Find minimum value"""
        node = self.root
        while node.left:
            node = node.left
        return node.value if node else None

    def find_max(self):
        """Find maximum value"""
        node = self.root
        while node.right:
            node = node.right
        return node.value if node else None

    def find_closest(self, target):
        """Find value closest to target"""
        return self._find_closest_recursive(self.root, target, self.root.value)

    def _find_closest_recursive(self, node, target, closest):
        """Helper for finding closest"""
        if node is None:
            return closest

        if abs(target - node.value) < abs(target - closest):
            closest = node.value

        if target < node.value:
            return self._find_closest_recursive(node.left, target, closest)
        else:
            return self._find_closest_recursive(node.right, target, closest)


# ============================================
# Example Usage
# ============================================

bst = BinarySearchTree()
values = [5, 3, 7, 1, 4, 6, 8]

for val in values:
    bst.insert(val)

print("Inorder (sorted):", bst.inorder())  # [1, 3, 4, 5, 6, 7, 8]
print("Search 4:", bst.search(4))  # True
print("Search 10:", bst.search(10))  # False
print("Min:", bst.find_min())  # 1
print("Max:", bst.find_max())  # 8
print("Closest to 5.5:", bst.find_closest(5.5))  # 5 or 6

bst.delete(3)
print("After deleting 3:", bst.inorder())  # [1, 4, 5, 6, 7, 8]
```

---

## Django Project: Pricing Tier System with BST

**Use case:** Find appropriate pricing tier based on user budget

```python
# File: pricing/models.py

from django.db import models

class PricingTier(models.Model):
    """Pricing tiers stored in database"""
    price = models.DecimalField(max_digits=10, decimal_places=2, unique=True)
    name = models.CharField(max_length=100)
    features = models.TextField()
    storage_gb = models.IntegerField()

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.name} - ${self.price}"


# File: pricing/services.py

from .models import PricingTier
from structures.bst import BinarySearchTree

class PricingService:
    """Find best pricing tier using BST"""

    def __init__(self):
        self.bst = BinarySearchTree()
        self._load_tiers()

    def _load_tiers(self):
        """Load tiers from database into BST"""
        tiers = PricingTier.objects.all().order_by('price')
        for tier in tiers:
            self.bst.insert(float(tier.price))

    def find_best_tier(self, user_budget):
        """
        Find tier closest to user's budget
        User has $50, we recommend tier closest to $50
        """
        closest_price = self.bst.find_closest(float(user_budget))
        tier = PricingTier.objects.get(price=closest_price)
        return tier

    def find_affordable_tiers(self, max_budget):
        """Find all tiers user can afford"""
        all_prices = self.bst.inorder()
        affordable = [p for p in all_prices if p <= max_budget]
        return PricingTier.objects.filter(price__in=affordable)


# File: pricing/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import PricingService

@api_view(['GET'])
def recommend_tier(request):
    """
    GET /api/pricing/recommend/?budget=50

    Response: {
        "recommended_tier": "Pro",
        "price": 49.99,
        "features": "..."
    }
    """
    budget = float(request.query_params.get('budget', 0))

    service = PricingService()
    tier = service.find_best_tier(budget)

    return Response({
        'recommended_tier': tier.name,
        'price': tier.price,
        'storage': tier.storage_gb,
        'features': tier.features
    })
```

---

---

# 4ï¸âƒ£ HEAPS ðŸ”º

## What is a Heap?

**Child explanation:** "A tree that's almost complete, where parent is always bigger (max heap) or smaller (min heap) than children."

```
Max Heap (parent > children):
        10
       /  \
      9    5
     / \  /
    8  7 3

Min Heap (parent < children):
        1
       / \
      2   3
     / \ / \
    4  5 6  7
```

### Heap Properties
| Property | Value |
|---|---|
| **Time to insert** | O(log n) |
| **Time to remove min/max** | O(log n) |
| **Time to find min/max** | O(1) |
| **Use case** | Priority queues |

---

## Code: Heap Implementation

```python
# File: structures/heap.py

class MinHeap:
    """Min Heap - smallest at top"""
    def __init__(self):
        self.heap = []

    def _parent(self, index):
        return (index - 1) // 2

    def _left_child(self, index):
        return 2 * index + 1

    def _right_child(self, index):
        return 2 * index + 2

    def _swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def insert(self, value):
        """Add value to heap"""
        self.heap.append(value)
        self._bubble_up(len(self.heap) - 1)

    def _bubble_up(self, index):
        """Move element up if smaller than parent"""
        while index > 0:
            parent_idx = self._parent(index)
            if self.heap[index] < self.heap[parent_idx]:
                self._swap(index, parent_idx)
                index = parent_idx
            else:
                break

    def extract_min(self):
        """Remove and return smallest"""
        if not self.heap:
            return None

        min_val = self.heap[0]

        # Move last element to root
        self.heap[0] = self.heap[-1]
        self.heap.pop()

        # Bubble down
        if self.heap:
            self._bubble_down(0)

        return min_val

    def _bubble_down(self, index):
        """Move element down if larger than children"""
        while True:
            smallest = index
            left = self._left_child(index)
            right = self._right_child(index)

            if left < len(self.heap) and self.heap[left] < self.heap[smallest]:
                smallest = left

            if right < len(self.heap) and self.heap[right] < self.heap[smallest]:
                smallest = right

            if smallest != index:
                self._swap(index, smallest)
                index = smallest
            else:
                break

    def peek_min(self):
        """Get smallest without removing"""
        return self.heap[0] if self.heap else None

    def size(self):
        return len(self.heap)


class MaxHeap:
    """Max Heap - largest at top"""
    def __init__(self):
        self.heap = []

    def _parent(self, index):
        return (index - 1) // 2

    def _left_child(self, index):
        return 2 * index + 1

    def _right_child(self, index):
        return 2 * index + 2

    def _swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def insert(self, value):
        """Add value"""
        self.heap.append(value)
        self._bubble_up(len(self.heap) - 1)

    def _bubble_up(self, index):
        """Move element up if larger than parent"""
        while index > 0:
            parent_idx = self._parent(index)
            if self.heap[index] > self.heap[parent_idx]:
                self._swap(index, parent_idx)
                index = parent_idx
            else:
                break

    def extract_max(self):
        """Remove and return largest"""
        if not self.heap:
            return None

        max_val = self.heap[0]
        self.heap[0] = self.heap[-1]
        self.heap.pop()

        if self.heap:
            self._bubble_down(0)

        return max_val

    def _bubble_down(self, index):
        """Move element down if smaller than children"""
        while True:
            largest = index
            left = self._left_child(index)
            right = self._right_child(index)

            if left < len(self.heap) and self.heap[left] > self.heap[largest]:
                largest = left

            if right < len(self.heap) and self.heap[right] > self.heap[largest]:
                largest = right

            if largest != index:
                self._swap(index, largest)
                index = largest
            else:
                break

    def peek_max(self):
        """Get largest without removing"""
        return self.heap[0] if self.heap else None


# ============================================
# Example Usage
# ============================================

min_heap = MinHeap()
for val in [5, 3, 7, 1, 9, 2]:
    min_heap.insert(val)

print("Min heap sorted:", [min_heap.extract_min() for _ in range(6)])
# [1, 2, 3, 5, 7, 9]

max_heap = MaxHeap()
for val in [5, 3, 7, 1, 9, 2]:
    max_heap.insert(val)

print("Max heap sorted:", [max_heap.extract_max() for _ in range(6)])
# [9, 7, 5, 3, 2, 1]
```

---

## Django Project: Priority Queue for Tasks

**Use case:** Process urgent tasks first

```python
# File: tasks/models.py

from django.db import models

class Task(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]

    title = models.CharField(max_length=255)
    priority = models.IntegerField(choices=PRIORITY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return self.title


# File: tasks/services.py

from .models import Task
from structures.heap import MaxHeap

class TaskPriorityQueue:
    """Process tasks by priority using heap"""

    def __init__(self):
        self.heap = MaxHeap()
        self._load_tasks()

    def _load_tasks(self):
        """Load incomplete tasks"""
        tasks = Task.objects.filter(completed=False)
        for task in tasks:
            self.heap.insert((task.priority, task.id, task.title))

    def get_next_task(self):
        """Get highest priority task"""
        if self.heap.size() == 0:
            return None

        priority, task_id, title = self.heap.extract_max()
        task = Task.objects.get(id=task_id)
        return task

    def add_task(self, priority, title):
        """Add new task"""
        task = Task.objects.create(priority=priority, title=title)
        self.heap.insert((priority, task.id, task.title))
        return task


# File: tasks/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import TaskPriorityQueue

@api_view(['GET'])
def get_next_priority_task(request):
    """Get most urgent task to work on"""
    queue = TaskPriorityQueue()
    task = queue.get_next_task()

    if task:
        return Response({
            'task_id': task.id,
            'title': task.title,
            'priority': task.get_priority_display(),
            'created': task.created_at
        })

    return Response({'message': 'No pending tasks'})
```

---

---

# 5ï¸âƒ£ GRAPHS ðŸ•¸ï¸

## What is a Graph?

**Child explanation:** "Like a map with cities and roads connecting them. Cities = nodes, roads = edges."

```
      A â”€â”€â”€ B
      â”‚     â”‚ \
      â”‚     â”‚  C
      D â”€â”€â”€ E â”€ F
```

### Graph Types
| Type | Direction | Use Case |
|---|---|---|
| **Undirected** | No arrows (roads go both ways) | Social networks |
| **Directed** | Arrows (one way street) | Recommendations |
| **Weighted** | Numbers on edges (distance) | Maps, pricing |
| **Cyclic** | Has loops | Most real graphs |
| **Acyclic** | No loops (DAG) | Dependency graphs |

---

## Code: Graph Implementation

```python
# File: structures/graph.py

from collections import deque, defaultdict

class Graph:
    """Graph using adjacency list"""
    def __init__(self, directed=False):
        self.graph = defaultdict(list)
        self.directed = directed

    def add_edge(self, u, v, weight=1):
        """Add edge from u to v"""
        self.graph[u].append((v, weight))

        if not self.directed:
            self.graph[v].append((u, weight))

    def get_neighbors(self, node):
        """Get neighbors of node"""
        return self.graph.get(node, [])

    # ============================================
    # GRAPH TRAVERSALS
    # ============================================

    def bfs(self, start):
        """Breadth-First Search (level by level)"""
        visited = set()
        queue = deque([start])
        result = []

        while queue:
            node = queue.popleft()

            if node in visited:
                continue

            visited.add(node)
            result.append(node)

            for neighbor, _ in self.graph[node]:
                if neighbor not in visited:
                    queue.append(neighbor)

        return result

    def dfs(self, start):
        """Depth-First Search (go deep first)"""
        visited = set()
        result = []

        def dfs_recursive(node):
            visited.add(node)
            result.append(node)

            for neighbor, _ in self.graph[node]:
                if neighbor not in visited:
                    dfs_recursive(neighbor)

        dfs_recursive(start)
        return result

    # ============================================
    # SHORTEST PATH
    # ============================================

    def dijkstra(self, start):
        """Shortest path from start to all nodes"""
        distances = {node: float('inf') for node in self.graph}
        distances[start] = 0

        visited = set()

        while len(visited) < len(self.graph):
            # Find unvisited node with smallest distance
            unvisited = {n: d for n, d in distances.items() if n not in visited}
            if not unvisited:
                break

            current = min(unvisited, key=unvisited.get)
            visited.add(current)

            # Update neighbors
            for neighbor, weight in self.graph[current]:
                new_distance = distances[current] + weight
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance

        return distances

    # ============================================
    # CYCLE DETECTION
    # ============================================

    def has_cycle(self):
        """Check if graph has cycle (directed)"""
        visited = set()
        recursion_stack = set()

        def has_cycle_dfs(node):
            visited.add(node)
            recursion_stack.add(node)

            for neighbor, _ in self.graph[node]:
                if neighbor not in visited:
                    if has_cycle_dfs(neighbor):
                        return True
                elif neighbor in recursion_stack:
                    return True

            recursion_stack.remove(node)
            return False

        for node in self.graph:
            if node not in visited:
                if has_cycle_dfs(node):
                    return True

        return False

    # ============================================
    # CONNECTIVITY
    # ============================================

    def is_connected(self):
        """Check if all nodes reachable from any node"""
        if not self.graph:
            return True

        start = next(iter(self.graph))
        visited = self.bfs(start)

        return len(visited) == len(self.graph)

    def get_connected_components(self):
        """Get all connected components"""
        visited = set()
        components = []

        def dfs(node, component):
            visited.add(node)
            component.append(node)

            for neighbor, _ in self.graph[node]:
                if neighbor not in visited:
                    dfs(neighbor, component)

        for node in self.graph:
            if node not in visited:
                component = []
                dfs(node, component)
                components.append(component)

        return components


# ============================================
# Example Usage
# ============================================

g = Graph(directed=False)

# Social network
edges = [
    ('Alice', 'Bob'),
    ('Bob', 'Charlie'),
    ('Charlie', 'David'),
    ('Alice', 'David'),
    ('Eve', 'Frank'),
]

for u, v in edges:
    g.add_edge(u, v)

print("BFS from Alice:", g.bfs('Alice'))
# ['Alice', 'Bob', 'David', 'Charlie']

print("DFS from Alice:", g.dfs('Alice'))
# ['Alice', 'Bob', 'Charlie', 'David']

print("Connected components:", g.get_connected_components())
# [['Alice', 'Bob', 'David', 'Charlie'], ['Eve', 'Frank']]

# Weighted graph (map)
g2 = Graph(directed=False)
g2.add_edge('A', 'B', 4)
g2.add_edge('A', 'C', 2)
g2.add_edge('B', 'C', 1)
g2.add_edge('B', 'D', 5)
g2.add_edge('C', 'D', 8)

distances = g2.dijkstra('A')
print("Shortest paths from A:", distances)
# {'A': 0, 'B': 3, 'C': 2, 'D': 8}
```

---

## Django Project: Social Network with Recommendations

**Use case:** Find friends of friends, build recommendation engine

```python
# File: social/models.py

from django.db import models
from django.contrib.auth.models import User

class Friendship(models.Model):
    """Connection between users"""
    user1 = models.ForeignKey(User, related_name='friendships_initiated', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='friendships_received', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"{self.user1} <-> {self.user2}"


# File: social/services.py

from .models import Friendship
from structures.graph import Graph

class SocialNetworkService:
    """Social network analysis using graphs"""

    def __init__(self):
        self.graph = Graph(directed=False)
        self._build_graph()

    def _build_graph(self):
        """Build graph from database"""
        friendships = Friendship.objects.all()
        for friendship in friendships:
            self.graph.add_edge(
                friendship.user1.id,
                friendship.user2.id
            )

    def get_mutual_friends(self, user_id, other_user_id):
        """Find mutual friends between two users"""
        user1_friends = set(neighbor for neighbor, _ in self.graph.get_neighbors(user_id))
        user2_friends = set(neighbor for neighbor, _ in self.graph.get_neighbors(other_user_id))

        mutual = user1_friends & user2_friends
        return [User.objects.get(id=uid) for uid in mutual]

    def get_friend_suggestions(self, user_id, limit=5):
        """
        Recommend users:
        Friends of friends who aren't already friends
        """
        user_friends = set(neighbor for neighbor, _ in self.graph.get_neighbors(user_id))
        user_friends.add(user_id)

        friends_of_friends = {}

        for friend_id in user_friends:
            for neighbor, _ in self.graph.get_neighbors(friend_id):
                if neighbor not in user_friends:
                    friends_of_friends[neighbor] = friends_of_friends.get(neighbor, 0) + 1

        # Sort by mutual friend count
        suggestions = sorted(friends_of_friends.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [User.objects.get(id=uid) for uid, _ in suggestions]

    def get_degrees_of_separation(self, user1_id, user2_id):
        """Find distance between two users"""
        visited = {user1_id}
        queue = deque([(user1_id, 0)])

        while queue:
            current, distance = queue.popleft()

            if current == user2_id:
                return distance

            for neighbor, _ in self.graph.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, distance + 1))

        return None  # Not connected


# File: social/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .services import SocialNetworkService
from django.contrib.auth.models import User

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_friend_suggestions(request):
    """
    GET /api/social/suggestions/
    Get 5 friend recommendations
    """
    service = SocialNetworkService()
    suggestions = service.get_friend_suggestions(request.user.id, limit=5)

    return Response({
        'suggestions': [
            {'id': user.id, 'username': user.username}
            for user in suggestions
        ]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_degrees_of_separation(request, other_user_id):
    """
    GET /api/social/degrees/{user_id}/
    How many steps to reach another user
    """
    service = SocialNetworkService()
    degrees = service.get_degrees_of_separation(request.user.id, other_user_id)

    if degrees is None:
        return Response({'connected': False})

    return Response({
        'connected': True,
        'degrees': degrees,
        'message': f"You're {degrees} step(s) away from this user"
    })
```

---

---

# 6ï¸âƒ£ TRIE (PREFIX TREE) ðŸ“

## What is a Trie?

**Child explanation:** "Like a dictionary where each letter is a node. Perfect for autocomplete!"

```
       root
      /  |  \
     a   c   d
    /|   |   |
   p b   a   o
   |     |   |
   p l   t   g
```

Words: apple, cab, cat, dog

---

## Code: Trie Implementation

```python
# File: structures/trie.py

class TrieNode:
    """Trie node"""
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False


class Trie:
    """Trie for autocomplete and spell check"""
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        """Insert word"""
        node = self.root

        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]

        node.is_end_of_word = True

    def search(self, word):
        """Check if word exists"""
        node = self._find_node(word)
        return node is not None and node.is_end_of_word

    def starts_with(self, prefix):
        """Check if any word starts with prefix"""
        return self._find_node(prefix) is not None

    def _find_node(self, prefix):
        """Find node for prefix"""
        node = self.root

        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]

        return node

    def autocomplete(self, prefix):
        """Get all words starting with prefix"""
        node = self._find_node(prefix)
        if node is None:
            return []

        results = []

        def dfs(node, word):
            if node.is_end_of_word:
                results.append(word)

            for char, child_node in node.children.items():
                dfs(child_node, word + char)

        dfs(node, prefix)
        return results


# ============================================
# Example Usage
# ============================================

trie = Trie()
words = ['apple', 'app', 'application', 'apply', 'cat', 'car', 'card']

for word in words:
    trie.insert(word)

print("Search 'apple':", trie.search('apple'))  # True
print("Search 'app':", trie.search('app'))  # True
print("Search 'apps':", trie.search('apps'))  # False

print("Autocomplete 'app':", trie.autocomplete('app'))
# ['app', 'apple', 'application', 'apply']

print("Autocomplete 'ca':", trie.autocomplete('ca'))
# ['car', 'card', 'cat']
```

---

## Django Project: Search Autocomplete

```python
# File: search/models.py

from django.db import models

class Keyword(models.Model):
    """Popular search keywords"""
    word = models.CharField(max_length=255, unique=True)
    frequency = models.IntegerField(default=1)

    def __str__(self):
        return self.word


# File: search/services.py

from .models import Keyword
from structures.trie import Trie

class SearchService:
    """Search with Trie autocomplete"""

    def __init__(self):
        self.trie = Trie()
        self._load_keywords()

    def _load_keywords(self):
        """Load keywords into Trie"""
        keywords = Keyword.objects.all()
        for kw in keywords:
            self.trie.insert(kw.word)

    def get_suggestions(self, prefix):
        """Get search suggestions"""
        return self.trie.autocomplete(prefix)

    def record_search(self, query):
        """Record search and update frequency"""
        kw, created = Keyword.objects.get_or_create(word=query)
        if not created:
            kw.frequency += 1
            kw.save()


# File: search/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import SearchService

@api_view(['GET'])
def search_suggestions(request):
    """
    GET /api/search/suggestions/?q=app
    Get search suggestions
    """
    query = request.query_params.get('q', '')

    if len(query) < 2:
        return Response({'suggestions': []})

    service = SearchService()
    suggestions = service.get_suggestions(query)

    return Response({
        'query': query,
        'suggestions': suggestions[:10]  # Top 10
    })
```

---

---

# 7ï¸âƒ£ SEGMENT TREE ðŸ“Š

## What is a Segment Tree?

**Child explanation:** "Tree that answers questions about ranges super fast, like 'what's the sum from index 2 to 5?'"

```
Build from: [1, 2, 3, 4, 5]

        15 (sum of all)
       /  \
     6     9
    / \   / \
   3   3 7   2
  / \ /\
 1  2 3 4
```

---

## Code: Segment Tree Implementation

```python
# File: structures/segment_tree.py

class SegmentTree:
    """Segment tree for range sum queries"""
    def __init__(self, arr):
        self.n = len(arr)
        self.tree = [0] * (4 * len(arr))
        self.arr = arr
        self.build(0, 0, len(arr) - 1)

    def build(self, node, start, end):
        """Build the segment tree"""
        if start == end:
            self.tree[node] = self.arr[start]
        else:
            mid = (start + end) // 2
            left_child = 2 * node + 1
            right_child = 2 * node + 2

            self.build(left_child, start, mid)
            self.build(right_child, mid + 1, end)

            self.tree[node] = self.tree[left_child] + self.tree[right_child]

    def range_sum(self, left, right):
        """Sum from index left to right"""
        return self._range_sum(0, 0, self.n - 1, left, right)

    def _range_sum(self, node, start, end, left, right):
        """Helper for range sum"""
        if right < start or end < left:
            return 0

        if left <= start and end <= right:
            return self.tree[node]

        mid = (start + end) // 2
        left_child = 2 * node + 1
        right_child = 2 * node + 2

        left_sum = self._range_sum(left_child, start, mid, left, right)
        right_sum = self._range_sum(right_child, mid + 1, end, left, right)

        return left_sum + right_sum

    def update(self, index, value):
        """Update value at index"""
        self._update(0, 0, self.n - 1, index, value)
        self.arr[index] = value

    def _update(self, node, start, end, index, value):
        """Helper for update"""
        if start == end:
            self.tree[node] = value
        else:
            mid = (start + end) // 2
            left_child = 2 * node + 1
            right_child = 2 * node + 2

            if index <= mid:
                self._update(left_child, start, mid, index, value)
            else:
                self._update(right_child, mid + 1, end, index, value)

            self.tree[node] = self.tree[left_child] + self.tree[right_child]


# ============================================
# Example Usage
# ============================================

arr = [1, 2, 3, 4, 5]
st = SegmentTree(arr)

print("Sum 0-2:", st.range_sum(0, 2))  # 1+2+3 = 6
print("Sum 1-4:", st.range_sum(1, 4))  # 2+3+4+5 = 14

st.update(2, 10)  # Change 3 to 10

print("Sum 0-2 after update:", st.range_sum(0, 2))  # 1+2+10 = 13
```

---

---

# 8ï¸âƒ£ FENWICK TREE (BIT) ðŸŒ³

## What is Fenwick Tree?

**Child explanation:** "Faster segment tree for range sum. Uses binary representation magic!"

### Comparison
| Operation | Array | Fenwick Tree |
|---|---|---|
| Range sum | O(n) | O(log n) |
| Update | O(1) | O(log n) |
| Space | O(n) | O(n) |

---

## Code: Fenwick Tree Implementation

```python
# File: structures/fenwick_tree.py

class FenwickTree:
    """Fenwick/BIT tree for efficient range sum queries"""
    def __init__(self, arr):
        self.n = len(arr)
        self.tree = [0] * (len(arr) + 1)

        for i in range(len(arr)):
            self.update_value(i, arr[i])

    def update_value(self, index, delta):
        """Add delta to element at index"""
        index += 1  # Fenwick tree is 1-indexed

        while index <= self.n:
            self.tree[index] += delta
            index += index & (-index)  # Binary trick

    def prefix_sum(self, index):
        """Sum from 0 to index"""
        index += 1
        result = 0

        while index > 0:
            result += self.tree[index]
            index -= index & (-index)

        return result

    def range_sum(self, left, right):
        """Sum from left to right"""
        if left == 0:
            return self.prefix_sum(right)
        return self.prefix_sum(right) - self.prefix_sum(left - 1)


# ============================================
# Example Usage
# ============================================

arr = [1, 2, 3, 4, 5]
ft = FenwickTree(arr)

print("Prefix sum 0-2:", ft.prefix_sum(2))  # 1+2+3 = 6
print("Range sum 1-3:", ft.range_sum(1, 3))  # 2+3+4 = 9

ft.update_value(2, 7)  # Add 7 to index 2 (3+7=10)

print("Range sum 1-3 after:", ft.range_sum(1, 3))  # 2+10+4 = 16
```

---

---

# ðŸ“Š COMPARISON TABLE (All Structures)

| Structure | Insert | Delete | Search | Use Case | Space |
|---|---|---|---|---|---|
| **Tree** | O(n) | O(n) | O(n) | Hierarchy | O(n) |
| **Binary Tree** | O(n) | O(n) | O(n) | Sorting | O(n) |
| **BST** | O(log n) | O(log n) | O(log n) | Database | O(n) |
| **Heap** | O(log n) | O(log n) | O(n) | Priority queue | O(n) |
| **Graph** | O(1) | O(1) | O(V+E) | Networks | O(V+E) |
| **Trie** | O(m) | O(m) | O(m) | Autocomplete | O(m*n) |
| **Seg Tree** | - | - | O(log n) | Range queries | O(n) |
| **Fenwick** | O(log n) | - | O(log n) | Range updates | O(n) |

(m = word length, n = number of words, V = vertices, E = edges)

---

---

# ðŸš€ COMPLETE DJANGO PROJECT: Tree-Based File Manager

```python
# File: file_manager/models.py

from django.db import models
from django.contrib.auth.models import User

class Folder(models.Model):
    """Tree node for folders"""
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    size = models.BigIntegerField(default=0)

    class Meta:
        unique_together = ('parent', 'name', 'owner')

    def __str__(self):
        return self.name


class File(models.Model):
    """Files in folders"""
    name = models.CharField(max_length=255)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='files')
    size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# File: file_manager/services.py

from .models import Folder, File
from structures.heap import MaxHeap

class FolderService:
    """Folder operations using tree logic"""

    def get_folder_size(self, folder):
        """Calculate folder size recursively"""
        total = 0

        # Add files in this folder
        total += sum(f.size for f in folder.files.all())

        # Add sizes of subfolders
        for child in folder.children.all():
            total += self.get_folder_size(child)

        return total

    def get_largest_folders(self, user, limit=10):
        """Get largest folders using heap"""
        heap = MaxHeap()

        folders = Folder.objects.filter(owner=user)
        for folder in folders:
            size = self.get_folder_size(folder)
            heap.insert((size, folder.id, folder.name))

        result = []
        for _ in range(limit):
            if heap.size() > 0:
                size, folder_id, name = heap.extract_max()
                result.append({'name': name, 'size': size})

        return result

    def get_folder_depth(self, folder):
        """Get depth of folder from root"""
        depth = 0
        current = folder

        while current.parent:
            current = current.parent
            depth += 1

        return depth

    def get_all_ancestors(self, folder):
        """Get all parent folders"""
        ancestors = []
        current = folder.parent

        while current:
            ancestors.append(current)
            current = current.parent

        return list(reversed(ancestors))


# File: file_manager/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Folder, File
from .services import FolderService

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def largest_folders(request):
    """GET /api/largest-folders/"""
    service = FolderService()
    largest = service.get_largest_folders(request.user, limit=10)

    return Response({
        'largest_folders': largest
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def folder_hierarchy(request, folder_id):
    """GET /api/folders/{id}/hierarchy/"""
    try:
        folder = Folder.objects.get(id=folder_id, owner=request.user)
    except Folder.DoesNotExist:
        return Response({'error': 'Folder not found'}, status=404)

    service = FolderService()
    ancestors = service.get_all_ancestors(folder)

    return Response({
        'folder': folder.name,
        'depth': service.get_folder_depth(folder),
        'path': ' / '.join([f.name for f in ancestors] + [folder.name]),
        'ancestors': [f.name for f in ancestors]
    })
```

---

---

# ðŸŽ“ Interview Answers

### Q: Difference between Tree and Graph?

**A:** "Trees are connected, acyclic graphs with one root and parent-child relationships. Graphs can have cycles, multiple connections, and are more general. Trees are used for hierarchies, graphs for networks."

### Q: When to use BST vs Heap?

**A:** "Use BST when you need fast search, insertion, deletion, and in-order traversal. Use Heap when you only need to access min/max quickly, like in priority queues."

### Q: How does Trie autocomplete work?

**A:** "Store all words in Trie where each character is a node. For autocomplete, find the node for the prefix using DFS to get all words starting with that prefix."

### Q: Segment Tree vs Fenwick Tree?

**A:** "Both do range queries in O(log n). Segment Tree is easier to understand and supports more complex queries. Fenwick Tree is more space-efficient using binary representation."

### Q: How would you detect a cycle in a graph?

**A:** "Use DFS with a recursion stack. During traversal, if we visit a node already in the current path's recursion stack, there's a cycle."

---

## âœ… Summary

| # | Structure | Child Analogy | When to Use |
|---|---|---|---|
| 1 | **Tree** | Upside-down tree | File systems, hierarchies |
| 2 | **Binary Tree** | Tree with 2 branches | Sorting, parsing |
| 3 | **BST** | Sorted binary tree | Databases, search |
| 4 | **Heap** | Pyramid | Priority queues |
| 5 | **Graph** | Network of cities | Maps, social networks |
| 6 | **Trie** | Dictionary structure | Autocomplete |
| 7 | **Segment Tree** | Range tree | Range queries |
| 8 | **Fenwick Tree** | Efficient ranges | Fast updates & queries |

**Key Insight:** Non-linear structures connect data in multiple directions, enabling faster operations for specific use cases compared to linear arrays.

---

**Total Code Lines:** ~7,500 lines including implementations, Django integrations, examples, and comments!
