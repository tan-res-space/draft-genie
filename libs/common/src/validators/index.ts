import { ValidationError } from '../errors';

// Email validation
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// UUID validation
export function isValidUUID(uuid: string): boolean {
  const uuidRegex =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
}

// Validate required fields
export function validateRequired(
  data: Record<string, any>,
  requiredFields: string[],
): void {
  const missingFields = requiredFields.filter(
    (field) => data[field] === undefined || data[field] === null || data[field] === '',
  );

  if (missingFields.length > 0) {
    throw new ValidationError(`Missing required fields: ${missingFields.join(', ')}`);
  }
}

// Validate number range
export function validateNumberRange(
  value: number,
  min: number,
  max: number,
  fieldName: string,
): void {
  if (value < min || value > max) {
    throw new ValidationError(
      `${fieldName} must be between ${min} and ${max}, got ${value}`,
    );
  }
}

// Validate string length
export function validateStringLength(
  value: string,
  min: number,
  max: number,
  fieldName: string,
): void {
  if (value.length < min || value.length > max) {
    throw new ValidationError(
      `${fieldName} length must be between ${min} and ${max}, got ${value.length}`,
    );
  }
}

// Validate enum value
export function validateEnum<T>(
  value: any,
  enumType: Record<string, T>,
  fieldName: string,
): void {
  const validValues = Object.values(enumType);
  if (!validValues.includes(value)) {
    throw new ValidationError(
      `${fieldName} must be one of: ${validValues.join(', ')}, got ${value}`,
    );
  }
}

// Validate array not empty
export function validateArrayNotEmpty<T>(array: T[], fieldName: string): void {
  if (!Array.isArray(array) || array.length === 0) {
    throw new ValidationError(`${fieldName} must be a non-empty array`);
  }
}

// Validate date range
export function validateDateRange(startDate: Date, endDate: Date): void {
  if (startDate > endDate) {
    throw new ValidationError('Start date must be before end date');
  }
}

// Validate pagination parameters
export function validatePagination(page?: number, limit?: number): void {
  if (page !== undefined && page < 1) {
    throw new ValidationError('Page must be greater than 0');
  }

  if (limit !== undefined && (limit < 1 || limit > 100)) {
    throw new ValidationError('Limit must be between 1 and 100');
  }
}

