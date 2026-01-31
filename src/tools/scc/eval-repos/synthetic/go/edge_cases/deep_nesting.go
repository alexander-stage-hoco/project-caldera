// Package edge_cases provides deep nesting tests.
package edge_cases

// DeeplyNestedFunction has 10+ levels of nesting.
func DeeplyNestedFunction(data map[string]interface{}) string {
	result := ""

	if data != nil { // Level 1
		if level1, ok := data["level1"]; ok { // Level 2
			if items, ok := level1.([]map[string]interface{}); ok { // Level 3
				for _, item := range items { // Level 4
					for key, value := range item { // Level 5
						if value != nil { // Level 6
							_ = key
							switch v := value.(type) { // Level 7
							case []int:
								for _, n := range v { // Level 8
									if n > 0 { // Level 9
										temp := n
										for temp > 0 { // Level 10
											if temp%2 == 0 { // Level 11
												result += string(rune('0' + temp%10))
											}
											temp--
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

	return result
}

// ProcessMatrix has deep nesting with matrix processing.
func ProcessMatrix(matrix [][][]map[string]interface{}) int {
	total := 0

	if matrix != nil { // 1
		for _, row := range matrix { // 2
			if row != nil { // 3
				for _, cell := range row { // 4
					if cell != nil { // 5
						for _, item := range cell { // 6
							for _, v := range item { // 7
								if v != nil { // 8
									switch num := v.(type) { // 9
									case int:
										if num > 0 { // 10
											for i := 0; i < num; i++ { // 11
												if i%2 == 1 { // 12
													total += i
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

	return total
}
