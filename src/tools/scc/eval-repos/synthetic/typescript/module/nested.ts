/**
 * Nested module demonstrating imports and exports in TypeScript.
 */

import { BinarySearchTree, Comparator } from '../massive';

interface NestedItem {
  id: number;
  name: string;
  createdAt: Date;
}

class NestedService {
  private tree: BinarySearchTree<NestedItem>;

  constructor() {
    const comparator: Comparator<NestedItem> = (a, b) => a.id - b.id;
    this.tree = new BinarySearchTree(comparator);
  }

  add(item: NestedItem): void {
    this.tree.insert(item);
  }

  find(id: number): NestedItem | null {
    return this.tree.find({ id, name: '', createdAt: new Date() });
  }

  getAll(): NestedItem[] {
    return this.tree.inorderTraversal();
  }
}

interface NestedProcessor<T, R> {
  process(input: T): Promise<R>;
}

class AsyncNestedProcessor implements NestedProcessor<NestedItem, boolean> {
  async process(input: NestedItem): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 10));
    return input.id > 0;
  }
}

export { NestedService, NestedItem, NestedProcessor, AsyncNestedProcessor };
