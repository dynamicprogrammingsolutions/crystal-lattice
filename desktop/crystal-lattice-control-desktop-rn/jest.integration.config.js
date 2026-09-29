const base = require('./jest.config');

module.exports = {
  ...base,
  testPathIgnorePatterns: ['/node_modules/', '<rootDir>/__native__/'],
  testMatch: ['<rootDir>/__integration__/**/*.integration.test.ts?(x)'],
};