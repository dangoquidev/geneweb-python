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

/**
 * Person response from API
 */
export interface PersonResponse {
  id: string;
  first_name: string;
  surname: string;
  sex: string;
  birth_date?: {
    year?: number;
    month?: number;
    day?: number;
    calendar?: string;
  };
  birth_place?: string;
  death_date?: {
    year?: number;
    month?: number;
    day?: number;
    calendar?: string;
  };
  death_place?: string;
  occupation?: string;
  public_name?: string;
  aliases?: string[];
  titles?: string[];
  family_id?: string;
  family_ids?: string[];
  events?: any[];
  access_level?: string;
}

/**
 * Family response from API
 */
export interface FamilyResponse {
  id: string;
  father_id?: string;
  mother_id?: string;
  children_ids?: string[];
  marriage_date?: {
    year?: number;
    month?: number;
    day?: number;
    calendar?: string;
  };
  marriage_place?: string;
  divorce_date?: {
    year?: number;
    month?: number;
    day?: number;
    calendar?: string;
  };
  notes?: string;
}

/**
 * Database statistics response
 */
export interface DatabaseStatisticsResponse {
  database_name: string;
  persons_count: number;
  families_count: number;
  oldest_birth_year?: number;
  newest_birth_year?: number;
}

/**
 * List all persons in a specific database
 *
 * @param databaseName - Database name
 * @param skip - Number of persons to skip
 * @param limit - Maximum number of persons to return
 * @returns Promise with list of persons
 * @throws ApiError if database not found or request fails
 */
export async function listDatabasePersons(
  databaseName: string,
  skip = 0,
  limit = 100
): Promise<PersonResponse[]> {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
  });
  const response = await fetch(
    `${API_BASE}/databases/${encodeURIComponent(databaseName)}/persons?${params}`
  );
  return handleResponse<PersonResponse[]>(response);
}

/**
 * Get a specific person from a database
 *
 * @param databaseName - Database name
 * @param personId - Person ID
 * @returns Promise with person details
 * @throws ApiError if database or person not found
 */
export async function getDatabasePerson(
  databaseName: string,
  personId: string
): Promise<PersonResponse> {
  const response = await fetch(
    `${API_BASE}/databases/${encodeURIComponent(databaseName)}/persons/${encodeURIComponent(personId)}`
  );
  return handleResponse<PersonResponse>(response);
}

/**
 * List all families in a specific database
 *
 * @param databaseName - Database name
 * @param skip - Number of families to skip
 * @param limit - Maximum number of families to return
 * @returns Promise with list of families
 * @throws ApiError if database not found or request fails
 */
export async function listDatabaseFamilies(
  databaseName: string,
  skip = 0,
  limit = 100
): Promise<FamilyResponse[]> {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
  });
  const response = await fetch(
    `${API_BASE}/databases/${encodeURIComponent(databaseName)}/families?${params}`
  );
  return handleResponse<FamilyResponse[]>(response);
}

/**
 * Get a specific family from a database
 *
 * @param databaseName - Database name
 * @param familyId - Family ID
 * @returns Promise with family details
 * @throws ApiError if database or family not found
 */
export async function getDatabaseFamily(
  databaseName: string,
  familyId: string
): Promise<FamilyResponse> {
  const response = await fetch(
    `${API_BASE}/databases/${encodeURIComponent(databaseName)}/families/${encodeURIComponent(familyId)}`
  );
  return handleResponse<FamilyResponse>(response);
}

/**
 * Get statistics for a specific database
 *
 * @param databaseName - Database name
 * @returns Promise with database statistics
 * @throws ApiError if database not found
 */
export async function getDatabaseStatistics(
  databaseName: string
): Promise<DatabaseStatisticsResponse> {
  const response = await fetch(
    `${API_BASE}/databases/${encodeURIComponent(databaseName)}/statistics`
  );
  return handleResponse<DatabaseStatisticsResponse>(response);
}
