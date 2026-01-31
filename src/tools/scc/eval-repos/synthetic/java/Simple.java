package synthetic.java;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Simple Java class demonstrating basic patterns.
 */
public class Simple {

    /**
     * A simple user class with basic fields.
     */
    public static class User {
        private final int id;
        private final String name;
        private final String email;
        private boolean active;

        public User(int id, String name, String email) {
            this.id = id;
            this.name = name;
            this.email = email;
            this.active = true;
        }

        public int getId() {
            return id;
        }

        public String getName() {
            return name;
        }

        public String getEmail() {
            return email;
        }

        public boolean isActive() {
            return active;
        }

        public void setActive(boolean active) {
            this.active = active;
        }

        public String greet() {
            return String.format("Hello, %s!", name);
        }

        public boolean isValid() {
            return id > 0 && name != null && !name.isEmpty() && email != null && email.contains("@");
        }

        @Override
        public String toString() {
            return String.format("User{id=%d, name='%s', email='%s', active=%b}", id, name, email, active);
        }
    }

    /**
     * A simple counter implementation.
     */
    public static class Counter {
        private int value;

        public Counter() {
            this(0);
        }

        public Counter(int initial) {
            this.value = initial;
        }

        public void increment() {
            value++;
        }

        public void decrement() {
            value--;
        }

        public int getValue() {
            return value;
        }

        public void reset() {
            value = 0;
        }
    }

    /**
     * Status enum representing different states.
     */
    public enum Status {
        PENDING("pending"),
        ACTIVE("active"),
        COMPLETED("completed"),
        FAILED("failed");

        private final String value;

        Status(String value) {
            this.value = value;
        }

        public String getValue() {
            return value;
        }

        public boolean isSuccess() {
            return this == COMPLETED;
        }

        public boolean isFailure() {
            return this == FAILED;
        }
    }

    // Utility methods

    public static int add(int a, int b) {
        return a + b;
    }

    public static int multiply(int a, int b) {
        return a * b;
    }

    public static int divide(int a, int b) throws ArithmeticException {
        if (b == 0) {
            throw new ArithmeticException("Division by zero");
        }
        return a / b;
    }

    public static List<User> filterActiveUsers(List<User> users) {
        return users.stream()
                .filter(User::isActive)
                .collect(Collectors.toList());
    }

    public static List<String> mapUserNames(List<User> users) {
        return users.stream()
                .map(User::getName)
                .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        // Create some users
        List<User> users = new ArrayList<>();
        users.add(new User(1, "Alice", "alice@example.com"));
        users.add(new User(2, "Bob", "bob@example.com"));
        users.add(new User(3, "Charlie", "charlie@example.com"));

        // Deactivate one user
        users.get(1).setActive(false);

        // Filter active users
        List<User> activeUsers = filterActiveUsers(users);
        System.out.println("Active users: " + activeUsers.size());

        // Map to names
        List<String> names = mapUserNames(activeUsers);
        System.out.println("Names: " + names);

        // Test counter
        Counter counter = new Counter(10);
        counter.increment();
        counter.increment();
        System.out.println("Counter value: " + counter.getValue());

        // Test status
        Status status = Status.ACTIVE;
        System.out.println("Status: " + status.getValue());
    }
}
