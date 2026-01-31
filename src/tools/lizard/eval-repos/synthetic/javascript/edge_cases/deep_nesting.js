/**
 * Deep nesting test - 10+ levels of indentation.
 */

function deeplyNestedFunction(data) {
  let result = '';

  if (data) {
    // Level 1
    if (data.level1) {
      // Level 2
      for (const item of data.level1) {
        // Level 3
        if (typeof item === 'object') {
          // Level 4
          for (const [key, value] of Object.entries(item)) {
            // Level 5
            if (value) {
              // Level 6
              try {
                // Level 7
                if (Array.isArray(value)) {
                  // Level 8
                  for (const v of value) {
                    // Level 9
                    if (v > 0) {
                      // Level 10
                      let temp = v;
                      while (temp > 0) {
                        // Level 11
                        if (temp % 2 === 0) {
                          // Level 12
                          result += temp.toString();
                        }
                        temp--;
                      }
                    }
                  }
                }
              } catch (e) {
                // Ignored
              }
            }
          }
        }
      }
    }
  }

  return result;
}

class DeeplyNestedClass {
  processMatrix(matrix) {
    let total = 0;

    if (matrix) {
      // 1
      for (const row of matrix) {
        // 2
        if (row) {
          // 3
          for (const cell of row) {
            // 4
            if (typeof cell === 'object') {
              // 5
              for (const [k, v] of Object.entries(cell)) {
                // 6
                if (v !== null) {
                  // 7
                  switch (typeof v) {
                    // 8
                    case 'number':
                      if (v > 0) {
                        // 9
                        for (let i = 0; i < v; i++) {
                          // 10
                          if (i % 2 === 1) {
                            // 11
                            total += i;
                          }
                        }
                      }
                      break;
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

module.exports = {
  deeplyNestedFunction,
  DeeplyNestedClass,
};
