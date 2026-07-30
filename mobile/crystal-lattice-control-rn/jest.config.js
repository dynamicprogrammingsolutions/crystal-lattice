module.exports = {
  preset: "react-native",
  setupFilesAfterEnv: ["./jest.setup.js"],
  moduleNameMapper: {
    "^react$": "<rootDir>/node_modules/react",
    "^react/jsx-runtime$": "<rootDir>/node_modules/react/jsx-runtime",
    "^react-native$": "<rootDir>/node_modules/react-native",
    "^@babel/runtime/(.*)$": "<rootDir>/node_modules/@babel/runtime/$1",
    "^@crystal-lattice/frontend-sdk$":
      "<rootDir>/../../packages/frontend-sdk/src",
    "^@crystal-lattice/frontend-sdk-react$":
      "<rootDir>/../../packages/frontend-sdk-react/src",
    "^@crystal-lattice/frontend-rn-components$":
      "<rootDir>/../../packages/frontend-rn-components/src",
  },
  testPathIgnorePatterns: [
    "/node_modules/",
    "<rootDir>/__integration__/",
    "<rootDir>/e2e/",
  ],
  transformIgnorePatterns: [
    "node_modules/(?!(@react-native|react-native|@react-native-community|@crystal-lattice/frontend-sdk|@crystal-lattice/frontend-sdk-react|react-native-url-polyfill)/)",
  ],
};
