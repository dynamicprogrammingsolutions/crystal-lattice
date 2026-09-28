const base = require('./jest.config');

module.exports = {
  ...base,
  testPathIgnorePatterns: ['/node_modules/'],
  testMatch: ['<rootDir>/__native__/**/*.native.test.ts'],
};
