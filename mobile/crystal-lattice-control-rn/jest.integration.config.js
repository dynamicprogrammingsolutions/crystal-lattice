const base = require('./jest.config');

module.exports = {
  ...base,
  testMatch: ['<rootDir>/__integration__/**/*.integration.test.ts?(x)'],
  testPathIgnorePatterns: ['/node_modules/'],
  testTimeout: 180000,
};
