/**
 * Logging interceptor for comprehensive request/response tracking.
 * 
 * This interceptor captures:
 * - Request details (method, path, headers, body)
 * - Response details (status code, duration)
 * - Request/response correlation via request ID
 * - Performance metrics
 */

import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Logger,
} from '@nestjs/common';
import { Observable, throwError } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { Request, Response } from 'express';

// Extend Express Request type to include user property
declare module 'express' {
  interface Request {
    user?: any;
  }
}
import { v4 as uuidv4 } from 'uuid';

interface RequestLogData {
  timestamp: string;
  event: string;
  request_id: string;
  method: string;
  path: string;
  url: string;
  query?: any;
  headers: any;
  body?: any;
  params?: any;
  user?: any;
  ip?: string;
}

interface ResponseLogData {
  timestamp: string;
  event: string;
  request_id: string;
  method: string;
  path: string;
  statusCode: number;
  duration_ms: number;
  response_size?: number;
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

  return data;
}

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HTTP');
  private readonly logRequestBody: boolean;
  private readonly maxBodySize: number;

  constructor(
    logRequestBody: boolean = true,
    _logResponseBody: boolean = false, // Prefixed with _ to indicate intentionally unused
    maxBodySize: number = 10000,
  ) {
    this.logRequestBody = logRequestBody;
    // logResponseBody parameter kept for backward compatibility but not used
    this.maxBodySize = maxBodySize;
  }

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const ctx = context.switchToHttp();
    const request = ctx.getRequest<Request>();
    const response = ctx.getResponse<Response>();

    // Generate or extract request ID
    const requestId = (request.headers['x-request-id'] as string) || uuidv4();
    
    // Add request ID to request object for downstream use
    (request as any).requestId = requestId;
    
    // Add request ID to response headers
    response.setHeader('X-Request-Id', requestId);

    // Start timing
    const startTime = Date.now();

    // Log incoming request
    this.logRequest(request, requestId);

    return next.handle().pipe(
      tap((data) => {
        // Log successful response
        const duration = Date.now() - startTime;
        this.logResponse(request, response, requestId, duration, data);
      }),
      catchError((error) => {
        // Log error response
        const duration = Date.now() - startTime;
        this.logError(request, response, requestId, duration, error);
        return throwError(() => error);
      }),
    );
  }

  private logRequest(request: Request, requestId: string): void {
    const logData: RequestLogData = {
      timestamp: new Date().toISOString(),
      event: 'request_received',
      request_id: requestId,
      method: request.method,
      path: request.path,
      url: request.url,
      query: request.query,
      headers: redactSensitiveData(request.headers),
      params: request.params,
      user: request.user ? { id: (request.user as any).id } : undefined,
      ip: request.ip || request.socket.remoteAddress,
    };

    // Log request body if enabled and method is POST/PUT/PATCH
    if (
      this.logRequestBody &&
      ['POST', 'PUT', 'PATCH'].includes(request.method) &&
      request.body
    ) {
      const bodySize = JSON.stringify(request.body).length;
      if (bodySize <= this.maxBodySize) {
        logData.body = redactSensitiveData(request.body);
      } else {
        logData.body = { _truncated: `Body too large (${bodySize} bytes)` };
      }
    }

    this.logger.log(
      `${request.method} ${request.path}`,
      JSON.stringify(logData, null, 2),
    );
  }

  private logResponse(
    request: Request,
    response: Response,
    requestId: string,
    duration: number,
    data?: any,
  ): void {
    const logData: ResponseLogData = {
      timestamp: new Date().toISOString(),
      event: 'request_completed',
      request_id: requestId,
      method: request.method,
      path: request.path,
      statusCode: response.statusCode,
      duration_ms: duration,
    };

    // Add response size if available
    if (data) {
      try {
        logData.response_size = JSON.stringify(data).length;
      } catch (e) {
        // Ignore if data is not serializable
      }
    }

    // Determine log level based on status code
    const logLevel = this.getLogLevel(response.statusCode);
    const message = `${request.method} ${request.path} - ${response.statusCode} (${duration}ms)`;

    if (logLevel === 'error') {
      this.logger.error(message, JSON.stringify(logData, null, 2));
    } else if (logLevel === 'warn') {
      this.logger.warn(message, JSON.stringify(logData, null, 2));
    } else {
      this.logger.log(message, JSON.stringify(logData, null, 2));
    }
  }

  private logError(
    request: Request,
    _response: Response, // Prefixed with _ to indicate intentionally unused
    requestId: string,
    duration: number,
    error: any,
  ): void {
    const logData = {
      timestamp: new Date().toISOString(),
      event: 'request_failed',
      request_id: requestId,
      method: request.method,
      path: request.path,
      duration_ms: duration,
      error: {
        type: error.constructor?.name || 'Error',
        message: error.message || String(error),
        statusCode: error.status || 500,
        stack: error.stack,
      },
      request: {
        method: request.method,
        path: request.path,
        query: request.query,
        headers: redactSensitiveData(request.headers),
        body: redactSensitiveData(request.body),
      },
    };

    this.logger.error(
      `${request.method} ${request.path} - Error: ${error.message}`,
      JSON.stringify(logData, null, 2),
    );
  }

  private getLogLevel(statusCode: number): 'log' | 'warn' | 'error' {
    if (statusCode >= 500) {
      return 'error';
    } else if (statusCode >= 400) {
      return 'warn';
    }
    return 'log';
  }
}

