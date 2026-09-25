import js from '@eslint/js'
import prettier from 'eslint-config-prettier'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import globals from 'globals'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist', 'coverage', 'playwright-report', 'test-results', 'src/api/schema.d.ts'] },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: {
      ecmaVersion: 2023,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-explicit-any': 'error',
      // Tokens live in the httpOnly cookie; never in web storage (SHARED_CONTEXT §9.8).
      'no-restricted-globals': [
        'error',
        {
          name: 'localStorage',
          message: 'Auth lives in the httpOnly cookie. Do not use web storage.',
        },
        {
          name: 'sessionStorage',
          message: 'Auth lives in the httpOnly cookie. Do not use web storage.',
        },
      ],
    },
  },
  prettier,
)
