import { Test, TestingModule } from '@nestjs/testing';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { UnauthorizedException, ConflictException } from '@nestjs/common';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AuthService,
        {
          provide: JwtService,
          useValue: {
            sign: jest.fn().mockReturnValue('mock-jwt-token'),
          },
        },
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn((key: string) => {
              const config: Record<string, string> = {
                JWT_SECRET: 'test-secret',
                JWT_EXPIRES_IN: '24h',
                API_KEYS: 'test-key-1,test-key-2',
              };
              return config[key];
            }),
          },
        },
      ],
    }).compile();

    service = module.get<AuthService>(AuthService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('register', () => {
    it('should register a new user successfully', async () => {
      const registerDto = {
        email: 'test@example.com',
        password: 'password123',
        name: 'Test User',
      };

      const result = await service.register(registerDto);

      expect(result).toHaveProperty('accessToken');
      expect(result).toHaveProperty('refreshToken');
      expect(result).toHaveProperty('user');
      expect(result.user.email).toBe(registerDto.email);
      expect(result.user.name).toBe(registerDto.name);
      expect(result.user.role).toBe('user');
    });

    it('should throw ConflictException if user already exists', async () => {
      const registerDto = {
        email: 'admin@draftgenie.com', // Default admin user
        password: 'password123',
        name: 'Test User',
      };

      await expect(service.register(registerDto)).rejects.toThrow(ConflictException);
    });
  });

  describe('login', () => {
    it('should login successfully with valid credentials', async () => {
      const loginDto = {
        email: 'admin@draftgenie.com',
        password: 'admin123',
      };

      const result = await service.login(loginDto);

      expect(result).toHaveProperty('accessToken');
      expect(result).toHaveProperty('refreshToken');
      expect(result.user.email).toBe(loginDto.email);
    });

    it('should throw UnauthorizedException with invalid email', async () => {
      const loginDto = {
        email: 'nonexistent@example.com',
        password: 'password123',
      };

      await expect(service.login(loginDto)).rejects.toThrow(UnauthorizedException);
    });

    it('should throw UnauthorizedException with invalid password', async () => {
      const loginDto = {
        email: 'admin@draftgenie.com',
        password: 'wrongpassword',
      };

      await expect(service.login(loginDto)).rejects.toThrow(UnauthorizedException);
    });
  });

  describe('refreshToken', () => {
    it('should refresh token successfully', async () => {
      // First login to get a refresh token
      const loginResult = await service.login({
        email: 'admin@draftgenie.com',
        password: 'admin123',
      });

      const result = await service.refreshToken({
        refreshToken: loginResult.refreshToken,
      });

      expect(result).toHaveProperty('accessToken');
      expect(result).toHaveProperty('refreshToken');
      expect(result.refreshToken).not.toBe(loginResult.refreshToken); // Should be a new token
    });

    it('should throw UnauthorizedException with invalid refresh token', async () => {
      await expect(
        service.refreshToken({ refreshToken: 'invalid-token' })
      ).rejects.toThrow(UnauthorizedException);
    });
  });

  describe('validateApiKey', () => {
    it('should validate correct API key', async () => {
      const result = await service.validateApiKey('test-key-1');
      expect(result).toBe(true);
    });

    it('should reject invalid API key', async () => {
      const result = await service.validateApiKey('invalid-key');
      expect(result).toBe(false);
    });
  });

  describe('logout', () => {
    it('should logout successfully', async () => {
      const loginResult = await service.login({
        email: 'admin@draftgenie.com',
        password: 'admin123',
      });

      await service.logout(loginResult.refreshToken);

      // Try to use the refresh token after logout
      await expect(
        service.refreshToken({ refreshToken: loginResult.refreshToken })
      ).rejects.toThrow(UnauthorizedException);
    });
  });
});

