package synthetic.module;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

/**
 * Nested module demonstrating Java module patterns.
 */
public class Nested {

    /**
     * Represents a nested item.
     */
    public static class NestedItem {
        private final int id;
        private final String name;
        private final long createdAt;

        public NestedItem(int id, String name, long createdAt) {
            this.id = id;
            this.name = name;
            this.createdAt = createdAt;
        }

        public int getId() {
            return id;
        }

        public String getName() {
            return name;
        }

        public long getCreatedAt() {
            return createdAt;
        }
    }

    /**
     * Service for managing nested items.
     */
    public static class NestedService {
        private final List<NestedItem> items = new ArrayList<>();
        private final ReadWriteLock lock = new ReentrantReadWriteLock();

        public void add(NestedItem item) {
            lock.writeLock().lock();
            try {
                items.add(item);
            } finally {
                lock.writeLock().unlock();
            }
        }

        public Optional<NestedItem> find(int id) {
            lock.readLock().lock();
            try {
                return items.stream()
                        .filter(item -> item.getId() == id)
                        .findFirst();
            } finally {
                lock.readLock().unlock();
            }
        }

        public List<NestedItem> getAll() {
            lock.readLock().lock();
            try {
                return new ArrayList<>(items);
            } finally {
                lock.readLock().unlock();
            }
        }

        public int clear() {
            lock.writeLock().lock();
            try {
                int count = items.size();
                items.clear();
                return count;
            } finally {
                lock.writeLock().unlock();
            }
        }
    }

    /**
     * Interface for processing items.
     */
    public interface NestedProcessor {
        boolean process(NestedItem item);
    }

    /**
     * Async processor implementation.
     */
    public static class AsyncProcessor implements NestedProcessor {
        @Override
        public boolean process(NestedItem item) {
            return item.getId() > 0;
        }
    }
}
