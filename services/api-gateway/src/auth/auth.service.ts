import { Injectable, UnauthorizedException, ConflictException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import * as bcrypt from 'bcrypt';
import { v4 as uuidv4 } from 'uuid';
import { LoginDto, RegisterDto, RefreshTokenDto } from './dto';
import { AuthResponse, JwtPayload, User } from './interfaces';

@Injectable()
export class AuthService {
  // In-memory user store (replace with database in production)
  private users: Map<string, User> = new Map();
  private refreshTokens: Map<string, string> = new Map(); // refreshToken -> userId

  constructor(
    private jwtService: JwtService,
    private configService: ConfigService,
  ) {
    // Create default admin user for testing
    this.createDefaultUser();
  }

  private async createDefaultUser() {
    const hashedPassword = await bcrypt.hash('admin123', 10);
    const adminUser: User = {
      id: uuidv4(),
      email: 'admin@draftgenie.com',
      password: hashedPassword,
      name: 'Admin User',
      role: 'admin',
      createdAt: new Date(),
    };
    this.users.set(adminUser.email, adminUser);
  }

  async register(registerDto: RegisterDto): Promise<AuthResponse> {
    const { email, password, name } = registerDto;

    // Check if user already exists
    if (this.users.has(email)) {
      throw new ConflictException('User with this email already exists');
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Create user
    const user: User = {
      id: uuidv4(),
      email,
      password: hashedPassword,
      name,
      role: 'user',
      createdAt: new Date(),
    };

    this.users.set(email, user);

    // Generate tokens
    return this.generateTokens(user);
  }

  async login(loginDto: LoginDto): Promise<AuthResponse> {
    const { email, password } = loginDto;

    // Find user
    const user = this.users.get(email);
    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }

    // Verify password
    const isPasswordValid = await bcrypt.compare(password, user.password);
    if (!isPasswordValid) {
      throw new UnauthorizedException('Invalid credentials');
    }

    // Generate tokens
    return this.generateTokens(user);
  }

  async refreshToken(refreshTokenDto: RefreshTokenDto): Promise<AuthResponse> {
    const { refreshToken } = refreshTokenDto;

    // Verify refresh token
    const userId = this.refreshTokens.get(refreshToken);
    if (!userId) {
      throw new UnauthorizedException('Invalid refresh token');
    }

    // Find user
    const user = Array.from(this.users.values()).find(u => u.id === userId);
    if (!user) {
      throw new UnauthorizedException('User not found');
    }

    // Remove old refresh token
    this.refreshTokens.delete(refreshToken);

    // Generate new tokens
    return this.generateTokens(user);
  }

  async validateUser(payload: JwtPayload): Promise<User> {
    const user = Array.from(this.users.values()).find(u => u.id === payload.sub);
    if (!user) {
      throw new UnauthorizedException('User not found');
    }
    return user;
  }

  async validateApiKey(apiKey: string): Promise<boolean> {
    const validApiKeys = this.configService.get<string>('API_KEYS')?.split(',') || [];
    return validApiKeys.includes(apiKey);
  }

  private async generateTokens(user: User): Promise<AuthResponse> {
    const payload: JwtPayload = {
      sub: user.id,
      email: user.email,
      role: user.role,
    };

    const accessToken = this.jwtService.sign(payload);
    const refreshToken = uuidv4();

    // Store refresh token
    this.refreshTokens.set(refreshToken, user.id);

    return {
      accessToken,
      refreshToken,
      expiresIn: this.configService.get<string>('JWT_EXPIRES_IN') || '24h',
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        role: user.role,
      },
    };
  }

  async logout(refreshToken: string): Promise<void> {
    this.refreshTokens.delete(refreshToken);
  }
}

