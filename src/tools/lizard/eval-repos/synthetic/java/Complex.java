package synthetic.java;

import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
import java.util.stream.*;

/**
 * Complex Java class demonstrating advanced patterns.
 * Includes generics, streams, annotations, and concurrency.
 */
public class Complex {

    // Generic repository interface
    public interface Repository<T, ID> {
        Optional<T> findById(ID id);
        List<T> findAll();
        T save(T entity);
        void delete(ID id);
        boolean exists(ID id);
    }

    // In-memory repository implementation
    public static class InMemoryRepository<T, ID> implements Repository<T, ID> {
        private final Map<ID, T> store = new ConcurrentHashMap<>();
        private final Function<T, ID> idExtractor;

        public InMemoryRepository(Function<T, ID> idExtractor) {
            this.idExtractor = idExtractor;
        }

        @Override
        public Optional<T> findById(ID id) {
            return Optional.ofNullable(store.get(id));
        }

        @Override
        public List<T> findAll() {
            return new ArrayList<>(store.values());
        }

        @Override
        public T save(T entity) {
            ID id = idExtractor.apply(entity);
            store.put(id, entity);
            return entity;
        }

        @Override
        public void delete(ID id) {
            store.remove(id);
        }

        @Override
        public boolean exists(ID id) {
            return store.containsKey(id);
        }
    }

    // Result type for error handling
    public static class Result<T, E> {
        private final T value;
        private final E error;
        private final boolean success;

        private Result(T value, E error, boolean success) {
            this.value = value;
            this.error = error;
            this.success = success;
        }

        public static <T, E> Result<T, E> ok(T value) {
            return new Result<>(value, null, true);
        }

        public static <T, E> Result<T, E> error(E error) {
            return new Result<>(null, error, false);
        }

        public boolean isSuccess() {
            return success;
        }

        public boolean isError() {
            return !success;
        }

        public T getValue() {
            if (!success) {
                throw new IllegalStateException("Result is an error");
            }
            return value;
        }

        public E getError() {
            if (success) {
                throw new IllegalStateException("Result is a success");
            }
            return error;
        }

        public <U> Result<U, E> map(Function<T, U> mapper) {
            if (success) {
                return Result.ok(mapper.apply(value));
            }
            return Result.error(error);
        }

        public <U> Result<U, E> flatMap(Function<T, Result<U, E>> mapper) {
            if (success) {
                return mapper.apply(value);
            }
            return Result.error(error);
        }

        public T orElse(T defaultValue) {
            return success ? value : defaultValue;
        }

        public T orElseGet(Supplier<T> supplier) {
            return success ? value : supplier.get();
        }
    }

    // Builder pattern with fluent API
    public static class RequestBuilder {
        private String method;
        private String url;
        private Map<String, String> headers = new HashMap<>();
        private String body;
        private int timeout = 30000;

        public RequestBuilder method(String method) {
            this.method = method;
            return this;
        }

        public RequestBuilder url(String url) {
            this.url = url;
            return this;
        }

        public RequestBuilder header(String key, String value) {
            this.headers.put(key, value);
            return this;
        }

        public RequestBuilder body(String body) {
            this.body = body;
            return this;
        }

        public RequestBuilder timeout(int timeout) {
            this.timeout = timeout;
            return this;
        }

        public Request build() {
            if (method == null || url == null) {
                throw new IllegalStateException("Method and URL are required");
            }
            return new Request(method, url, headers, body, timeout);
        }
    }

    public static class Request {
        private final String method;
        private final String url;
        private final Map<String, String> headers;
        private final String body;
        private final int timeout;

        Request(String method, String url, Map<String, String> headers, String body, int timeout) {
            this.method = method;
            this.url = url;
            this.headers = Collections.unmodifiableMap(new HashMap<>(headers));
            this.body = body;
            this.timeout = timeout;
        }

        public String getMethod() { return method; }
        public String getUrl() { return url; }
        public Map<String, String> getHeaders() { return headers; }
        public String getBody() { return body; }
        public int getTimeout() { return timeout; }
    }

    // Event system with type-safe events
    public interface Event {
        String getType();
        long getTimestamp();
    }

    public static abstract class BaseEvent implements Event {
        private final long timestamp = System.currentTimeMillis();

        @Override
        public long getTimestamp() {
            return timestamp;
        }
    }

    public static class UserCreatedEvent extends BaseEvent {
        private final int userId;
        private final String userName;

        public UserCreatedEvent(int userId, String userName) {
            this.userId = userId;
            this.userName = userName;
        }

        @Override
        public String getType() {
            return "USER_CREATED";
        }

        public int getUserId() { return userId; }
        public String getUserName() { return userName; }
    }

    public static class EventBus {
        private final Map<Class<? extends Event>, List<Consumer<? extends Event>>> handlers = new ConcurrentHashMap<>();
        private final ExecutorService executor = Executors.newCachedThreadPool();

        @SuppressWarnings("unchecked")
        public <E extends Event> void subscribe(Class<E> eventType, Consumer<E> handler) {
            handlers.computeIfAbsent(eventType, k -> new CopyOnWriteArrayList<>())
                    .add(handler);
        }

        @SuppressWarnings("unchecked")
        public <E extends Event> void publish(E event) {
            List<Consumer<? extends Event>> eventHandlers = handlers.get(event.getClass());
            if (eventHandlers != null) {
                for (Consumer<? extends Event> handler : eventHandlers) {
                    executor.submit(() -> ((Consumer<E>) handler).accept(event));
                }
            }
        }

        public void shutdown() {
            executor.shutdown();
        }
    }

    // Pipeline pattern for data processing
    public static class Pipeline<T> {
        private final List<Function<T, T>> stages = new ArrayList<>();

        public Pipeline<T> addStage(Function<T, T> stage) {
            stages.add(stage);
            return this;
        }

        public T execute(T input) {
            T result = input;
            for (Function<T, T> stage : stages) {
                result = stage.apply(result);
            }
            return result;
        }

        public CompletableFuture<T> executeAsync(T input, Executor executor) {
            return CompletableFuture.supplyAsync(() -> execute(input), executor);
        }
    }

    // Rate limiter implementation
    public static class RateLimiter {
        private final int maxRequests;
        private final long windowMillis;
        private final Queue<Long> requestTimestamps = new ConcurrentLinkedQueue<>();

        public RateLimiter(int maxRequests, long windowMillis) {
            this.maxRequests = maxRequests;
            this.windowMillis = windowMillis;
        }

        public synchronized boolean tryAcquire() {
            long now = System.currentTimeMillis();
            long windowStart = now - windowMillis;

            // Remove expired timestamps
            while (!requestTimestamps.isEmpty() && requestTimestamps.peek() < windowStart) {
                requestTimestamps.poll();
            }

            if (requestTimestamps.size() < maxRequests) {
                requestTimestamps.offer(now);
                return true;
            }

            return false;
        }

        public void acquire() throws InterruptedException {
            while (!tryAcquire()) {
                Thread.sleep(10);
            }
        }
    }

    // Circuit breaker pattern
    public static class CircuitBreaker {
        private enum State { CLOSED, OPEN, HALF_OPEN }

        private State state = State.CLOSED;
        private int failureCount = 0;
        private long lastFailureTime = 0;
        private final int failureThreshold;
        private final long resetTimeoutMillis;
        private final Object lock = new Object();

        public CircuitBreaker(int failureThreshold, long resetTimeoutMillis) {
            this.failureThreshold = failureThreshold;
            this.resetTimeoutMillis = resetTimeoutMillis;
        }

        public <T> T execute(Supplier<T> action) throws Exception {
            synchronized (lock) {
                if (state == State.OPEN) {
                    if (System.currentTimeMillis() - lastFailureTime > resetTimeoutMillis) {
                        state = State.HALF_OPEN;
                    } else {
                        throw new RuntimeException("Circuit breaker is OPEN");
                    }
                }
            }

            try {
                T result = action.get();
                synchronized (lock) {
                    if (state == State.HALF_OPEN) {
                        state = State.CLOSED;
                        failureCount = 0;
                    }
                }
                return result;
            } catch (Exception e) {
                synchronized (lock) {
                    failureCount++;
                    lastFailureTime = System.currentTimeMillis();
                    if (failureCount >= failureThreshold) {
                        state = State.OPEN;
                    }
                }
                throw e;
            }
        }

        public State getState() {
            synchronized (lock) {
                return state;
            }
        }
    }

    // Demonstration of stream operations
    public static class StreamOperations {
        public static <T> List<T> filterAndSort(List<T> items, Predicate<T> predicate, Comparator<T> comparator) {
            return items.stream()
                    .filter(predicate)
                    .sorted(comparator)
                    .collect(Collectors.toList());
        }

        public static <T, K> Map<K, List<T>> groupBy(List<T> items, Function<T, K> classifier) {
            return items.stream()
                    .collect(Collectors.groupingBy(classifier));
        }

        public static <T, R> List<R> flatMapAndDistinct(List<List<T>> nestedList, Function<T, R> mapper) {
            return nestedList.stream()
                    .flatMap(List::stream)
                    .map(mapper)
                    .distinct()
                    .collect(Collectors.toList());
        }

        public static <T> Optional<T> reduce(List<T> items, BinaryOperator<T> accumulator) {
            return items.stream().reduce(accumulator);
        }

        public static IntSummaryStatistics summarize(List<Integer> numbers) {
            return numbers.stream()
                    .mapToInt(Integer::intValue)
                    .summaryStatistics();
        }
    }

    public static void main(String[] args) {
        // Test Result type
        Result<Integer, String> success = Result.ok(42);
        Result<Integer, String> error = Result.error("Something went wrong");

        System.out.println("Success value: " + success.getValue());
        System.out.println("Error message: " + error.getError());

        // Test Pipeline
        Pipeline<String> pipeline = new Pipeline<String>()
                .addStage(String::toLowerCase)
                .addStage(String::trim)
                .addStage(s -> s.replace(" ", "_"));

        String result = pipeline.execute("  Hello World  ");
        System.out.println("Pipeline result: " + result);

        // Test EventBus
        EventBus eventBus = new EventBus();
        eventBus.subscribe(UserCreatedEvent.class, event ->
            System.out.println("User created: " + event.getUserName()));
        eventBus.publish(new UserCreatedEvent(1, "Alice"));

        // Clean up
        eventBus.shutdown();
    }
}
