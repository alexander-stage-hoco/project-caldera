/**
 * Complex JavaScript patterns - Medium complexity (CCN ~10-20)
 */

// Event emitter pattern
class EventEmitter {
  constructor() {
    this.events = new Map();
  }

  on(event, callback) {
    if (!this.events.has(event)) {
      this.events.set(event, []);
    }
    this.events.get(event).push(callback);
    return () => this.off(event, callback);
  }

  off(event, callback) {
    if (!this.events.has(event)) return;
    const callbacks = this.events.get(event);
    const index = callbacks.indexOf(callback);
    if (index > -1) {
      callbacks.splice(index, 1);
    }
  }

  emit(event, ...args) {
    if (!this.events.has(event)) return;
    for (const callback of this.events.get(event)) {
      try {
        callback(...args);
      } catch (error) {
        console.error(`Error in event handler: ${error.message}`);
      }
    }
  }
}

// State machine
class StateMachine {
  constructor(initialState, transitions) {
    this.state = initialState;
    this.transitions = transitions;
    this.emitter = new EventEmitter();
  }

  transition(action) {
    const stateTransitions = this.transitions[this.state];
    if (!stateTransitions) {
      throw new Error(`No transitions defined for state: ${this.state}`);
    }

    const nextState = stateTransitions[action];
    if (!nextState) {
      throw new Error(`Invalid action "${action}" for state "${this.state}"`);
    }

    const prevState = this.state;
    this.state = nextState;
    this.emitter.emit('transition', { from: prevState, to: nextState, action });

    return this.state;
  }

  onTransition(callback) {
    return this.emitter.on('transition', callback);
  }
}

// Async queue with concurrency control
class AsyncQueue {
  constructor(concurrency = 1) {
    this.concurrency = concurrency;
    this.running = 0;
    this.queue = [];
  }

  async add(task) {
    return new Promise((resolve, reject) => {
      this.queue.push({ task, resolve, reject });
      this.process();
    });
  }

  async process() {
    while (this.running < this.concurrency && this.queue.length > 0) {
      const { task, resolve, reject } = this.queue.shift();
      this.running++;

      try {
        const result = await task();
        resolve(result);
      } catch (error) {
        reject(error);
      } finally {
        this.running--;
        this.process();
      }
    }
  }
}

// Memoization with TTL
function memoizeWithTTL(fn, ttl = 60000) {
  const cache = new Map();

  return function (...args) {
    const key = JSON.stringify(args);
    const cached = cache.get(key);

    if (cached && Date.now() - cached.timestamp < ttl) {
      return cached.value;
    }

    const result = fn.apply(this, args);
    cache.set(key, { value: result, timestamp: Date.now() });

    // Cleanup old entries
    if (cache.size > 100) {
      const now = Date.now();
      for (const [k, v] of cache) {
        if (now - v.timestamp > ttl) {
          cache.delete(k);
        }
      }
    }

    return result;
  };
}

// Observable pattern
class Observable {
  constructor(subscribe) {
    this._subscribe = subscribe;
  }

  subscribe(observer) {
    const normalizedObserver =
      typeof observer === 'function'
        ? { next: observer, error: () => {}, complete: () => {} }
        : { next: () => {}, error: () => {}, complete: () => {}, ...observer };

    return this._subscribe(normalizedObserver);
  }

  map(fn) {
    return new Observable((observer) => {
      return this.subscribe({
        next: (value) => observer.next(fn(value)),
        error: (err) => observer.error(err),
        complete: () => observer.complete(),
      });
    });
  }

  filter(predicate) {
    return new Observable((observer) => {
      return this.subscribe({
        next: (value) => {
          if (predicate(value)) {
            observer.next(value);
          }
        },
        error: (err) => observer.error(err),
        complete: () => observer.complete(),
      });
    });
  }
}

module.exports = {
  EventEmitter,
  StateMachine,
  AsyncQueue,
  memoizeWithTTL,
  Observable,
};
