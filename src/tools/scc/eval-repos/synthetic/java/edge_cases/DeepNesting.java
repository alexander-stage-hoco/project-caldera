package synthetic.edge_cases;

import java.util.List;
import java.util.Map;

/**
 * Deep nesting test - 10+ levels of indentation.
 */
public class DeepNesting {

    public static String deeplyNestedFunction(Map<String, Object> data) {
        StringBuilder result = new StringBuilder();

        if (data != null) {  // Level 1
            Object level1 = data.get("level1");
            if (level1 instanceof List) {  // Level 2
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> items = (List<Map<String, Object>>) level1;
                for (Map<String, Object> item : items) {  // Level 3
                    if (item != null) {  // Level 4
                        for (Map.Entry<String, Object> entry : item.entrySet()) {  // Level 5
                            Object value = entry.getValue();
                            if (value != null) {  // Level 6
                                try {  // Level 7
                                    if (value instanceof List) {  // Level 8
                                        @SuppressWarnings("unchecked")
                                        List<Integer> numbers = (List<Integer>) value;
                                        for (Integer n : numbers) {  // Level 9
                                            if (n != null && n > 0) {  // Level 10
                                                int temp = n;
                                                while (temp > 0) {  // Level 11
                                                    if (temp % 2 == 0) {  // Level 12
                                                        result.append(temp);
                                                    }
                                                    temp--;
                                                }
                                            }
                                        }
                                    }
                                } catch (Exception e) {
                                    // Ignored
                                }
                            }
                        }
                    }
                }
            }
        }

        return result.toString();
    }

    public static int processMatrix(List<List<List<Map<String, Object>>>> matrix) {
        int total = 0;

        if (matrix != null) {  // 1
            for (List<List<Map<String, Object>>> row : matrix) {  // 2
                if (row != null) {  // 3
                    for (List<Map<String, Object>> cell : row) {  // 4
                        if (cell != null) {  // 5
                            for (Map<String, Object> item : cell) {  // 6
                                if (item != null) {  // 7
                                    for (Object v : item.values()) {  // 8
                                        if (v instanceof Integer) {  // 9
                                            int num = (Integer) v;
                                            if (num > 0) {  // 10
                                                for (int i = 0; i < num; i++) {  // 11
                                                    if (i % 2 == 1) {  // 12
                                                        total += i;
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        return total;
    }
}
