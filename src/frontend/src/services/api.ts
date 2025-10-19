/**
 * API Client for GenEWeb Backend
 *
 * Provides typed functions to interact with the REST API.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

/**
 * API error with status code and details
 */
export class ApiError extends Error {
  status: number;
  statusText: string;
  details?: any;

  constructor(
    status: number,
    statusText: string,
    details?: any
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
    this.details = details;
  }
}

/**
 * Database types
 */
export type DatabaseType = 'pickle' | 'sqlite';

/**
 * Database creation request
 */
export interface DatabaseCreateRequest {
  name: string;
  db_type?: DatabaseType;
}

/**
 * Database creation response
 */
export interface DatabaseCreateResponse {
  success: boolean;
  database_name: string;
  path: string;
  message: string;
}

/**
 * Database list response
 */
export interface DatabaseListResponse {
  databases: string[];
  count: number;
}

/**
 * Database info response
 */
export interface DatabaseInfoResponse {
  base_name: string;
  persons: number;
  families: number;
  path: string;
  version: string;
  created_date: string;
  modified_date: string;
}

/**
 * Helper function to handle fetch errors
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetails;
    try {
      errorDetails = await response.json();
    } catch {
      errorDetails = { message: response.statusText };
    }
    throw new ApiError(response.status, response.statusText, errorDetails);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

/**
 * List all available databases
 *
 * @returns Promise with list of database names
 * @throws ApiError if request fails
 */
export async function listDatabases(): Promise<DatabaseListResponse> {
  const response = await fetch(`${API_BASE}/databases`);
  return handleResponse<DatabaseListResponse>(response);
}

/**
 * Create a new database
 *
 * @param request - Database creation parameters
 * @returns Promise with creation result
 * @throws ApiError if validation fails or database exists
 *
 * @example
 * const result = await createDatabase({ name: 'ma_famille', db_type: 'pickle' });
 * console.log(result.message); // "Database 'ma_famille' created successfully"
 */
export async function createDatabase(
  request: DatabaseCreateRequest
): Promise<DatabaseCreateResponse> {
  const response = await fetch(`${API_BASE}/databases`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: request.name,
      db_type: request.db_type || 'pickle',
    }),
  });
  return handleResponse<DatabaseCreateResponse>(response);
}

/**
 * Get information about a specific database
 *
 * @param name - Database name
 * @returns Promise with database information
 * @throws ApiError if database not found
 */
export async function getDatabaseInfo(name: string): Promise<DatabaseInfoResponse> {
  const response = await fetch(`${API_BASE}/databases/${encodeURIComponent(name)}`);
  return handleResponse<DatabaseInfoResponse>(response);
}

/**
 * Delete a database
 *
 * @param name - Database name
 * @throws ApiError if database not found or deletion fails
 */
export async function deleteDatabase(name: string): Promise<void> {
  const response = await fetch(`${API_BASE}/databases/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  });
  return handleResponse<void>(response);
}

/**
 * Check API health status
 *
 * @returns Promise with health status
 */
export async function checkHealth(): Promise<{ status: string; timestamp: string }> {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse(response);
}
