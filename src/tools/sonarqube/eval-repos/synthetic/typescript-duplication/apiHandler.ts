// More duplicated TypeScript code for testing

interface ApiResponse {
  success: boolean;
  data: any;
  error?: string;
}

// Duplicated error handler 1
export function handleUserApiError(error: Error): ApiResponse {
  console.error('API Error:', error.message);

  if (error.message.includes('not found')) {
    return {
      success: false,
      data: null,
      error: 'Resource not found',
    };
  }

  if (error.message.includes('unauthorized')) {
    return {
      success: false,
      data: null,
      error: 'Unauthorized access',
    };
  }

  if (error.message.includes('timeout')) {
    return {
      success: false,
      data: null,
      error: 'Request timeout',
    };
  }

  return {
    success: false,
    data: null,
    error: 'Internal server error',
  };
}

// Duplicated error handler 2 - nearly identical
export function handleOrderApiError(error: Error): ApiResponse {
  console.error('API Error:', error.message);

  if (error.message.includes('not found')) {
    return {
      success: false,
      data: null,
      error: 'Resource not found',
    };
  }

  if (error.message.includes('unauthorized')) {
    return {
      success: false,
      data: null,
      error: 'Unauthorized access',
    };
  }

  if (error.message.includes('timeout')) {
    return {
      success: false,
      data: null,
      error: 'Request timeout',
    };
  }

  return {
    success: false,
    data: null,
    error: 'Internal server error',
  };
}

// Duplicated error handler 3 - nearly identical
export function handlePaymentApiError(error: Error): ApiResponse {
  console.error('API Error:', error.message);

  if (error.message.includes('not found')) {
    return {
      success: false,
      data: null,
      error: 'Resource not found',
    };
  }

  if (error.message.includes('unauthorized')) {
    return {
      success: false,
      data: null,
      error: 'Unauthorized access',
    };
  }

  if (error.message.includes('timeout')) {
    return {
      success: false,
      data: null,
      error: 'Request timeout',
    };
  }

  return {
    success: false,
    data: null,
    error: 'Internal server error',
  };
}

// Duplicated data formatter 1
export function formatUserResponse(data: any[]): any[] {
  return data.map(item => ({
    id: item.id,
    displayName: `${item.firstName} ${item.lastName}`,
    email: item.email.toLowerCase(),
    createdAt: new Date(item.createdAt).toISOString(),
    updatedAt: new Date(item.updatedAt).toISOString(),
  }));
}

// Duplicated data formatter 2
export function formatOrderResponse(data: any[]): any[] {
  return data.map(item => ({
    id: item.id,
    displayName: `${item.firstName} ${item.lastName}`,
    email: item.email.toLowerCase(),
    createdAt: new Date(item.createdAt).toISOString(),
    updatedAt: new Date(item.updatedAt).toISOString(),
  }));
}

// Duplicated data formatter 3
export function formatProductResponse(data: any[]): any[] {
  return data.map(item => ({
    id: item.id,
    displayName: `${item.firstName} ${item.lastName}`,
    email: item.email.toLowerCase(),
    createdAt: new Date(item.createdAt).toISOString(),
    updatedAt: new Date(item.updatedAt).toISOString(),
  }));
}
