//! Deep nesting test - 10+ levels of indentation.

use std::collections::HashMap;

/// Function with 10+ levels of nesting.
pub fn deeply_nested_function(data: Option<HashMap<String, Vec<HashMap<String, Vec<i32>>>>>) -> String {
    let mut result = String::new();

    if let Some(data) = data {  // Level 1
        if let Some(level1) = data.get("level1") {  // Level 2
            for item in level1 {  // Level 3
                for (key, value) in item {  // Level 4
                    let _ = key;
                    if !value.is_empty() {  // Level 5
                        for n in value {  // Level 6
                            if *n > 0 {  // Level 7
                                let mut temp = *n;
                                while temp > 0 {  // Level 8
                                    if temp % 2 == 0 {  // Level 9
                                        if temp < 100 {  // Level 10
                                            if temp > 0 {  // Level 11
                                                result.push_str(&temp.to_string());
                                            }
                                        }
                                    }
                                    temp -= 1;
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    result
}

/// Matrix processor with deep nesting.
pub fn process_matrix(matrix: Option<Vec<Vec<Vec<HashMap<String, i32>>>>>) -> i32 {
    let mut total = 0;

    if let Some(matrix) = matrix {  // 1
        for row in matrix {  // 2
            if !row.is_empty() {  // 3
                for cell in row {  // 4
                    if !cell.is_empty() {  // 5
                        for item in cell {  // 6
                            for (_, v) in item {  // 7
                                if v > 0 {  // 8
                                    for i in 0..v {  // 9
                                        if i % 2 == 1 {  // 10
                                            if i < 1000 {  // 11
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

    total
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_deeply_nested() {
        let result = deeply_nested_function(None);
        assert!(result.is_empty());
    }
}
