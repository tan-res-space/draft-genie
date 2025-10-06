module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/apps', '<rootDir>/libs'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  transform: {
    '^.+\\.ts$': 'ts-jest',
  },
  collectCoverageFrom: [
    '**/*.ts',
    '!**/*.spec.ts',
    '!**/*.test.ts',
    '!**/node_modules/**',
    '!**/dist/**',
    '!**/coverage/**',
  ],
  coverageDirectory: '<rootDir>/coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  moduleNameMapper: {
    '^@draft-genie/common$': '<rootDir>/libs/common/src/index.ts',
    '^@draft-genie/domain$': '<rootDir>/libs/domain/src/index.ts',
    '^@draft-genie/database$': '<rootDir>/libs/database/src/index.ts',
  },
  moduleFileExtensions: ['ts', 'js', 'json'],
  testTimeout: 30000,
};

