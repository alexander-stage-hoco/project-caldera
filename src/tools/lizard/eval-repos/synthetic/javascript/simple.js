/**
 * Sample JavaScript module for PoC testing.
 * Demonstrates ES6 features and moderate complexity.
 */

// Configuration
const CONFIG = {
  maxRetries: 3,
  timeout: 5000,
  debug: false,
};

/**
 * Simple logger utility.
 */
class Logger {
  constructor(prefix = '') {
    this.prefix = prefix;
  }

  log(message) {
    if (CONFIG.debug) {
      console.log(`[${this.prefix}] ${message}`);
    }
  }

  error(message) {
    console.error(`[${this.prefix}] ERROR: ${message}`);
  }
}

/**
 * Async task executor with retry logic.
 */
class TaskExecutor {
  constructor(options = {}) {
    this.maxRetries = options.maxRetries || CONFIG.maxRetries;
    this.timeout = options.timeout || CONFIG.timeout;
    this.logger = new Logger('TaskExecutor');
  }

  /**
   * Execute a task with retry logic.
   * @param {Function} task - Async task to execute
   * @returns {Promise<any>} - Result of the task
   */
  async execute(task) {
    let lastError;

    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        this.logger.log(`Attempt ${attempt}/${this.maxRetries}`);
        const result = await this.withTimeout(task());
        return result;
      } catch (error) {
        lastError = error;
        this.logger.error(`Attempt ${attempt} failed: ${error.message}`);

        if (attempt < this.maxRetries) {
          await this.delay(1000 * attempt);
        }
      }
    }

    throw new Error(`Task failed after ${this.maxRetries} attempts: ${lastError.message}`);
  }

  /**
   * Wrap a promise with a timeout.
   */
  withTimeout(promise) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`Task timed out after ${this.timeout}ms`));
      }, this.timeout);

      promise
        .then((result) => {
          clearTimeout(timer);
          resolve(result);
        })
        .catch((error) => {
          clearTimeout(timer);
          reject(error);
        });
    });
  }

  /**
   * Delay execution.
   */
  delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

/**
 * Data processor with various transformations.
 */
const DataProcessor = {
  /**
   * Filter an array based on predicate.
   */
  filter(array, predicate) {
    return array.filter(predicate);
  },

  /**
   * Map array elements.
   */
  map(array, mapper) {
    return array.map(mapper);
  },

  /**
   * Group array by key.
   */
  groupBy(array, keyFn) {
    return array.reduce((groups, item) => {
      const key = keyFn(item);
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(item);
      return groups;
    }, {});
  },

  /**
   * Calculate statistics for numeric array.
   */
  statistics(numbers) {
    if (numbers.length === 0) {
      return { count: 0, sum: 0, avg: 0, min: 0, max: 0 };
    }

    const sum = numbers.reduce((a, b) => a + b, 0);
    const avg = sum / numbers.length;
    const min = Math.min(...numbers);
    const max = Math.max(...numbers);

    return { count: numbers.length, sum, avg, min, max };
  },
};

// Export for use as module
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { Logger, TaskExecutor, DataProcessor, CONFIG };
}
