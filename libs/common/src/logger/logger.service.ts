import * as winston from 'winston';
import DailyRotateFile = require('winston-daily-rotate-file');

export interface LogContext {
  correlationId?: string;
  userId?: string;
  speakerId?: string;
  service?: string;
  [key: string]: any;
}

export class Logger {
  private logger: winston.Logger;
  private context: LogContext;

  constructor(context: LogContext = {}) {
    this.context = context;
    this.logger = this.createLogger();
  }

  private createLogger(): winston.Logger {
    const logFormat = winston.format.combine(
      winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
      winston.format.errors({ stack: true }),
      winston.format.splat(),
      winston.format.json(),
    );

    const transports: winston.transport[] = [
      new winston.transports.Console({
        format: winston.format.combine(
          winston.format.colorize(),
          winston.format.printf(({ timestamp, level, message, ...meta }) => {
            const contextStr = Object.keys(meta).length ? JSON.stringify(meta) : '';
            return `${timestamp} [${level}]: ${message} ${contextStr}`;
          }),
        ),
      }),
    ];

    // Add file rotation for production
    if (process.env.NODE_ENV === 'production') {
      transports.push(
        new DailyRotateFile({
          filename: 'logs/application-%DATE%.log',
          datePattern: 'YYYY-MM-DD',
          maxSize: '20m',
          maxFiles: '14d',
          format: logFormat,
        }),
      );

      transports.push(
        new DailyRotateFile({
          filename: 'logs/error-%DATE%.log',
          datePattern: 'YYYY-MM-DD',
          level: 'error',
          maxSize: '20m',
          maxFiles: '30d',
          format: logFormat,
        }),
      );
    }

    return winston.createLogger({
      level: process.env.LOG_LEVEL || 'info',
      format: logFormat,
      transports,
    });
  }

  private formatMessage(message: string, meta?: Record<string, any>): [string, Record<string, any>] {
    const combinedMeta = {
      ...this.context,
      ...meta,
    };
    return [message, combinedMeta];
  }

  debug(message: string, meta?: Record<string, any>): void {
    const [msg, combinedMeta] = this.formatMessage(message, meta);
    this.logger.debug(msg, combinedMeta);
  }

  info(message: string, meta?: Record<string, any>): void {
    const [msg, combinedMeta] = this.formatMessage(message, meta);
    this.logger.info(msg, combinedMeta);
  }

  warn(message: string, meta?: Record<string, any>): void {
    const [msg, combinedMeta] = this.formatMessage(message, meta);
    this.logger.warn(msg, combinedMeta);
  }

  error(message: string, error?: Error, meta?: Record<string, any>): void {
    const [msg, combinedMeta] = this.formatMessage(message, {
      ...meta,
      error: error?.message,
      stack: error?.stack,
    });
    this.logger.error(msg, combinedMeta);
  }

  setContext(context: LogContext): void {
    this.context = { ...this.context, ...context };
  }

  child(context: LogContext): Logger {
    return new Logger({ ...this.context, ...context });
  }
}

// Factory function for creating loggers
export function createLogger(context: LogContext = {}): Logger {
  return new Logger(context);
}

