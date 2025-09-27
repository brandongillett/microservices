import fs from 'fs';
import path from 'path';

// Token file paths
const TOKENS_DIR = './public/assets/tokens';
const OUTPUT_DIR = './src/tokens/generated';

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Load only the token files that exist and are being used
const loadTokenFile = (filename) => {
  const filePath = path.join(TOKENS_DIR, filename);
  return fs.existsSync(filePath) ? JSON.parse(fs.readFileSync(filePath, 'utf8')) : {};
};

const primitiveTokens = {
  color: loadTokenFile('color.json'),
  typography: loadTokenFile('typography.json'),
};

const semanticTokens = loadTokenFile('semantic.json');

function extractTokenValues(tokens) {
  if (typeof tokens !== 'object' || tokens === null) {
    return tokens;
  }

  if (tokens.value !== undefined) {
    return tokens.value;
  }

  const result = {};
  for (const [key, value] of Object.entries(tokens)) {
    result[key] = extractTokenValues(value);
  }
  return result;
}

function resolveTokenReferences(tokens, context) {
  if (typeof tokens === 'string') {
    // Check for token reference pattern
    const match = tokens.match(/^\{(.+)\}$/);
    if (match) {
      const tokenPath = match[1].split('.');
      let current = context;

      for (const segment of tokenPath) {
        if (current && typeof current === 'object' && segment in current) {
          current = current[segment];
        } else {
          console.warn(`Token reference not found: ${tokens}`);
          return tokens; // Return original if not found
        }
      }

      return current;
    }
  }

  if (typeof tokens === 'object' && tokens !== null) {
    const result = {};
    for (const [key, value] of Object.entries(tokens)) {
      result[key] = resolveTokenReferences(value, context);
    }
    return result;
  }

  return tokens;
}

console.log('Processing design tokens...');

const extractedPrimitives = {};
for (const [category, tokens] of Object.entries(primitiveTokens)) {
  if (Object.keys(tokens).length > 0) {
    extractedPrimitives[category] = extractTokenValues(tokens);
  }
}

const resolvedSemantic = Object.keys(semanticTokens).length > 0
  ? resolveTokenReferences(extractTokenValues(semanticTokens), extractedPrimitives)
  : {};

const primitiveExports = Object.entries(extractedPrimitives)
  .map(([key, value]) => `export const ${key} = ${JSON.stringify(value, null, 2)} as const;`)
  .join('\n\n');

const semanticExport = Object.keys(resolvedSemantic).length > 0
  ? `export const semantic = ${JSON.stringify(resolvedSemantic, null, 2)} as const;`
  : 'export const semantic = {} as const;';

const tokenIndexContent = `/**
 * Generated Design Tokens
 * This file is auto-generated. Do not edit manually.
 *
 * To regenerate, run: npm run build:tokens
 */

${primitiveExports}

${semanticExport}

// Unified token export
export const tokens = {
  ${Object.keys(extractedPrimitives).join(',\n  ')},
  semantic,
} as const;

export default tokens;

// Type exports for TypeScript support
export type Tokens = typeof tokens;
${Object.keys(extractedPrimitives).map(key => `export type ${key.charAt(0).toUpperCase() + key.slice(1)}Tokens = typeof ${key};`).join('\n')}
export type SemanticTokens = typeof semantic;
`;

// Write the main tokens file
fs.writeFileSync(path.join(OUTPUT_DIR, 'index.ts'), tokenIndexContent);

// Generate minimal JSON files
fs.writeFileSync(path.join(OUTPUT_DIR, 'primitives.json'), JSON.stringify(extractedPrimitives, null, 2));
if (Object.keys(resolvedSemantic).length > 0) {
  fs.writeFileSync(path.join(OUTPUT_DIR, 'semantic.json'), JSON.stringify(resolvedSemantic, null, 2));
}

console.log('Tokens generated successfully!');
console.log(`Generated files in: ${OUTPUT_DIR}`);
console.log('Files created:');
console.log('   - index.ts (main token exports)');
console.log('   - primitives.json');
if (Object.keys(resolvedSemantic).length > 0) {
  console.log('   - semantic.json');
}
console.log('\nUsage:');
console.log('   import { tokens } from "./tokens/generated";');
console.log('   const primaryColor = tokens.color.brand.primary;');
if (Object.keys(resolvedSemantic).length > 0) {
  console.log('   const buttonBg = tokens.semantic.button.primary.bg.default;');
}
