// TypeScript file with intentional code duplication for testing

interface DataRecord {
  id: number;
  name: string;
  value: number;
  timestamp: Date;
}

// Duplicated function 1
export function processUserData(data: DataRecord[]): DataRecord[] {
  const result: DataRecord[] = [];

  for (const item of data) {
    if (item.value > 0) {
      const processed: DataRecord = {
        id: item.id,
        name: item.name.toUpperCase(),
        value: item.value * 2,
        timestamp: new Date(),
      };
      result.push(processed);
    }
  }

  return result.sort((a, b) => a.value - b.value);
}

// Duplicated function 2 - nearly identical
export function processOrderData(data: DataRecord[]): DataRecord[] {
  const result: DataRecord[] = [];

  for (const item of data) {
    if (item.value > 0) {
      const processed: DataRecord = {
        id: item.id,
        name: item.name.toUpperCase(),
        value: item.value * 2,
        timestamp: new Date(),
      };
      result.push(processed);
    }
  }

  return result.sort((a, b) => a.value - b.value);
}

// Duplicated function 3 - nearly identical
export function processInventoryData(data: DataRecord[]): DataRecord[] {
  const result: DataRecord[] = [];

  for (const item of data) {
    if (item.value > 0) {
      const processed: DataRecord = {
        id: item.id,
        name: item.name.toUpperCase(),
        value: item.value * 2,
        timestamp: new Date(),
      };
      result.push(processed);
    }
  }

  return result.sort((a, b) => a.value - b.value);
}

// Duplicated function 4 - nearly identical
export function processTransactionData(data: DataRecord[]): DataRecord[] {
  const result: DataRecord[] = [];

  for (const item of data) {
    if (item.value > 0) {
      const processed: DataRecord = {
        id: item.id,
        name: item.name.toUpperCase(),
        value: item.value * 2,
        timestamp: new Date(),
      };
      result.push(processed);
    }
  }

  return result.sort((a, b) => a.value - b.value);
}

// Duplicated validation function 1
export function validateUserInput(input: string): boolean {
  if (!input) {
    return false;
  }
  if (input.length < 3) {
    return false;
  }
  if (input.length > 100) {
    return false;
  }
  if (!/^[a-zA-Z0-9]+$/.test(input)) {
    return false;
  }
  return true;
}

// Duplicated validation function 2
export function validateOrderInput(input: string): boolean {
  if (!input) {
    return false;
  }
  if (input.length < 3) {
    return false;
  }
  if (input.length > 100) {
    return false;
  }
  if (!/^[a-zA-Z0-9]+$/.test(input)) {
    return false;
  }
  return true;
}

// Duplicated validation function 3
export function validateProductInput(input: string): boolean {
  if (!input) {
    return false;
  }
  if (input.length < 3) {
    return false;
  }
  if (input.length > 100) {
    return false;
  }
  if (!/^[a-zA-Z0-9]+$/.test(input)) {
    return false;
  }
  return true;
}
