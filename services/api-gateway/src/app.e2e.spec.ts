import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from './app.module';

describe('API Gateway (e2e)', () => {
  let app: INestApplication;
  let accessToken: string;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    
    app.useGlobalPipes(
      new ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
      }),
    );

    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  describe('Health Checks', () => {
    it('/api/v1/health (GET)', () => {
      return request(app.getHttpServer())
        .get('/api/v1/health')
        .expect(200)
        .expect((res) => {
          expect(res.body).toHaveProperty('status');
        });
    });
  });

  describe('Authentication', () => {
    it('/api/v1/auth/login (POST) - should login with default admin', () => {
      return request(app.getHttpServer())
        .post('/api/v1/auth/login')
        .send({
          email: 'admin@draftgenie.com',
          password: 'admin123',
        })
        .expect(200)
        .expect((res) => {
          expect(res.body).toHaveProperty('accessToken');
          expect(res.body).toHaveProperty('refreshToken');
          expect(res.body).toHaveProperty('user');
          accessToken = res.body.accessToken;
        });
    });

    it('/api/v1/auth/login (POST) - should fail with invalid credentials', () => {
      return request(app.getHttpServer())
        .post('/api/v1/auth/login')
        .send({
          email: 'admin@draftgenie.com',
          password: 'wrongpassword',
        })
        .expect(401);
    });

    it('/api/v1/auth/register (POST) - should register new user', () => {
      return request(app.getHttpServer())
        .post('/api/v1/auth/register')
        .send({
          email: 'newuser@example.com',
          password: 'password123',
          name: 'New User',
        })
        .expect(201)
        .expect((res) => {
          expect(res.body).toHaveProperty('accessToken');
          expect(res.body.user.email).toBe('newuser@example.com');
        });
    });

    it('/api/v1/auth/register (POST) - should fail with duplicate email', () => {
      return request(app.getHttpServer())
        .post('/api/v1/auth/register')
        .send({
          email: 'admin@draftgenie.com',
          password: 'password123',
          name: 'Duplicate User',
        })
        .expect(409);
    });

    it('/api/v1/auth/me (GET) - should get current user profile', async () => {
      // First login
      const loginRes = await request(app.getHttpServer())
        .post('/api/v1/auth/login')
        .send({
          email: 'admin@draftgenie.com',
          password: 'admin123',
        });

      const token = loginRes.body.accessToken;

      return request(app.getHttpServer())
        .get('/api/v1/auth/me')
        .set('Authorization', `Bearer ${token}`)
        .expect(200)
        .expect((res) => {
          expect(res.body).toHaveProperty('email');
          expect(res.body.email).toBe('admin@draftgenie.com');
        });
    });

    it('/api/v1/auth/me (GET) - should fail without token', () => {
      return request(app.getHttpServer())
        .get('/api/v1/auth/me')
        .expect(401);
    });
  });

  describe('Protected Routes', () => {
    let token: string;

    beforeAll(async () => {
      const res = await request(app.getHttpServer())
        .post('/api/v1/auth/login')
        .send({
          email: 'admin@draftgenie.com',
          password: 'admin123',
        });
      token = res.body.accessToken;
    });

    it('should access aggregation endpoint with valid token', () => {
      return request(app.getHttpServer())
        .get('/api/v1/dashboard/metrics')
        .set('Authorization', `Bearer ${token}`)
        .expect((res) => {
          // May return 200 with data or errors depending on backend services
          expect([200, 503]).toContain(res.status);
        });
    });

    it('should reject aggregation endpoint without token', () => {
      return request(app.getHttpServer())
        .get('/api/v1/dashboard/metrics')
        .expect(401);
    });
  });

  describe('Validation', () => {
    it('should validate login DTO', () => {
      return request(app.getHttpServer())
        .post('/api/v1/auth/login')
        .send({
          email: 'invalid-email',
          password: '123', // Too short
        })
        .expect(400);
    });

    it('should validate register DTO', () => {
      return request(app.getHttpServer())
        .post('/api/v1/auth/register')
        .send({
          email: 'test@example.com',
          password: '123', // Too short
          // Missing name
        })
        .expect(400);
    });
  });
});

