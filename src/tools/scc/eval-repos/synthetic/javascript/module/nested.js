/**
 * Nested module demonstrating imports and exports.
 */

const { EventEmitter } = require('../complex');

class NestedService extends EventEmitter {
  constructor() {
    super();
    this.items = [];
  }

  add(item) {
    if (item != null) {
      this.items.push(item);
      this.emit('added', item);
    }
  }

  getAll() {
    return [...this.items];
  }

  find(predicate) {
    return this.items.find(predicate);
  }

  clear() {
    const count = this.items.length;
    this.items = [];
    this.emit('cleared', count);
  }
}

class NestedProcessor {
  async process(data) {
    await new Promise((resolve) => setTimeout(resolve, 10));
    return { processed: true, data };
  }
}

module.exports = {
  NestedService,
  NestedProcessor,
};
