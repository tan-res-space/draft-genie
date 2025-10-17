/**
 * Global exception filter for comprehensive error logging and handling.
 * 
 * This filter captures all unhandled exceptions and logs them with:
 * - Full stack traces
 * - Request context (method, path, headers, body)
 * - Error metadata
 * - Structured JSON format for automated analysis
 */

import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';

// Extend Express Request type to include user property
declare module 'express' {
  interface Request {
    user?: any;
  }
}

interface ErrorLogData {
  timestamp: string;
  level: string;
  severity: string;
  event: string;
  request_id?: string;
  error: {
    type: string;
    message: string;
    stack?: string;
    statusCode: number;
    details?: any;
  };
  request: {
    method: string;
    path: string;
    url: string;
    query?: any;
    headers: any;
    body?: any;
    params?: any;
    user?: any;
    ip?: string;
  };
  requires_investigation: boolean;
  alert_priority: string;
}

/**
 * Patterns for sensitive data that should be redacted from logs
 */
const SENSITIVE_PATTERNS = [
  /password/i,
  /passwd/i,
  /pwd/i,
  /secret/i,
  /token/i,
  /api[_-]?key/i,
  /authorization/i,
  /bearer/i,
  /jwt/i,
  /session/i,
  /cookie/i,
  /csrf/i,
  /ssn/i,
  /credit[_-]?card/i,
  /cvv/i,
  /pin/i,
  /private[_-]?key/i,
];

/**
 * Check if a field name contains sensitive information
 */
function isSensitiveField(fieldName: string): boolean {
  return SENSITIVE_PATTERNS.some(pattern => pattern.test(fieldName));
}

/**
 * Recursively redact sensitive information from data structures
 */
function redactSensitiveData(data: any, maxDepth: number = 10): any {
  if (maxDepth <= 0) {
    return '[MAX_DEPTH_REACHED]';
  }

  if (data === null || data === undefined) {
    return data;
  }

  if (typeof data === 'object') {
    if (Array.isArray(data)) {
      return data.map(item => redactSensitiveData(item, maxDepth - 1));
    }

    const redacted: any = {};
    for (const [key, value] of Object.entries(data)) {
      if (isSensitiveField(key)) {
        redacted[key] = '[REDACTED]';
      } else {
        redacted[key] = redactSensitiveData(value, maxDepth - 1);
      }
    }
    return redacted;
  }

  // Redact potential tokens in strings
  if (typeof data === 'string' && data.length > 20 && /^[A-Za-z0-9_\-\.]+$/.test(data)) {
    return `${data.substring(0, 8)}...[REDACTED]`;
  }

  return data;
}

/**
 * Extract request context for logging
 */
function extractRequestContext(request: Request): any {
  return {
    method: request.method,
    path: request.path,
    url: request.url,
    query: request.query,
    headers: redactSensitiveData(request.headers),
    body: redactSensitiveData(request.body),
    params: request.params,
    user: request.user ? { id: (request.user as any).id } : undefined,
    ip: request.ip || request.socket.remoteAddress,
  };
}

/**
 * Format exception details for logging
 */
function formatExceptionDetails(exception: any): any {
  const details: any = {
    type: exception.constructor?.name || 'Error',
    message: exception.message || String(exception),
    statusCode: exception.status || HttpStatus.INTERNAL_SERVER_ERROR,
  };

  // Add stack trace
  if (exception.stack) {
    details.stack = exception.stack;
    
    // Parse stack frames for structured logging
    const stackLines = exception.stack.split('\n').slice(1); // Skip first line (error message)
    details.stackFrames = stackLines.map((line: string) => {
      const match = line.match(/at\s+(.+?)\s+\((.+?):(\d+):(\d+)\)/);
      if (match) {
        return {
          function: match[1],
          file: match[2],
          line: parseInt(match[3]),
          column: parseInt(match[4]),
        };
      }
      return { raw: line.trim() };
    });
  }

  // Add HTTP exception details
  if (exception instanceof HttpException) {
    const response = exception.getResponse();
    details.httpResponse = typeof response === 'object' ? response : { message: response };
  }

  // Add custom exception properties
  const customProps = Object.keys(exception).filter(
    key => !['name', 'message', 'stack', 'status'].includes(key)
  );
  if (customProps.length > 0) {
    details.customProperties = {};
    customProps.forEach(key => {
      details.customProperties[key] = redactSensitiveData(exception[key]);
    });
  }

  return details;
}

@Catch()
export class GlobalExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger('GlobalExceptionFilter');

  catch(exception: any, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    // Determine status code
    const status =
      exception instanceof HttpException
        ? exception.getStatus()
        : HttpStatus.INTERNAL_SERVER_ERROR;

    // Extract request ID if available
    const requestId = request.headers['x-request-id'] as string;

    // Build comprehensive error log data
    const errorLogData: ErrorLogData = {
      timestamp: new Date().toISOString(),
      level: status >= 500 ? 'ERROR' : 'WARN',
      severity: status >= 500 ? 'ERROR' : 'WARNING',
      event: 'unhandled_exception',
      request_id: requestId,
      error: formatExceptionDetails(exception),
      request: extractRequestContext(request),
      requires_investigation: status >= 500,
      alert_priority: status >= 500 ? 'high' : 'medium',
    };

    // Log error with appropriate level
    if (status >= 500) {
      this.logger.error(
        `Server Error: ${exception.message || 'Unknown error'}`,
        JSON.stringify(errorLogData, null, 2)
      );
    } else if (status >= 400) {
      this.logger.warn(
        `Client Error: ${exception.message || 'Unknown error'}`,
        JSON.stringify(errorLogData, null, 2)
      );
    }

    // Build error response
    const errorResponse: any = {
      statusCode: status,
      timestamp: new Date().toISOString(),
      path: request.url,
      method: request.method,
      message: exception.message || 'Internal server error',
    };

    // Add request ID to response
    if (requestId) {
      errorResponse.requestId = requestId;
    }

    // Add detailed error info in development
    if (process.env.NODE_ENV === 'development') {
      errorResponse.error = exception.name;
      errorResponse.stack = exception.stack;
    }

    // Add HTTP exception response if available
    if (exception instanceof HttpException) {
      const exceptionResponse = exception.getResponse();
      if (typeof exceptionResponse === 'object') {
        Object.assign(errorResponse, exceptionResponse);
      }
    }

    // Set response headers
    response.setHeader('X-Request-Id', requestId || 'unknown');
    response.setHeader('Content-Type', 'application/json');

    // Send response
    response.status(status).json(errorResponse);
  }
}

