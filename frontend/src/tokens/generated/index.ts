/**
 * Generated Design Tokens
 * This file is auto-generated. Do not edit manually.
 *
 * To regenerate, run: npm run build:tokens
 */

export const color = {
  brand: {
    primary: '#EF476F',
    primaryDark: '#C7113C',
    primaryLight: '#F69CB1',
  },
  background: {
    default: '#2F2B3A',
    muted: '#615D6C',
    elevated: '#4A4559',
  },
  foreground: {
    default: '#F2F2F5',
    muted: '#BFBFCC',
    onAccent: '#2F2B3A',
  },
  border: {
    default: '#615D6C',
  },
  status: {
    info: '#3B82F6',
  },
} as const

export const typography = {
  fonts: {
    brand: {
      name: 'GeneralSans',
      family:
        "GeneralSans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      weights: {
        regular: {
          name: 'GeneralSans-Regular',
          weight: 400,
          style: 'normal',
          files: {
            woff: '/fonts/woff/GeneralSans-Regular.woff',
            woff2: '/fonts/woff2/GeneralSans-Regular.woff2',
          },
        },
        medium: {
          name: 'GeneralSans-Medium',
          weight: 500,
          style: 'normal',
          files: {
            woff: '/fonts/woff/GeneralSans-Medium.woff',
            woff2: '/fonts/woff2/GeneralSans-Medium.woff2',
          },
        },
        semibold: {
          name: 'GeneralSans-Semibold',
          weight: 600,
          style: 'normal',
          files: {
            woff: '/fonts/woff/GeneralSans-Semibold.woff',
            woff2: '/fonts/woff2/GeneralSans-Semibold.woff2',
          },
        },
        bold: {
          name: 'GeneralSans-Bold',
          weight: 700,
          style: 'normal',
          files: {
            woff: '/fonts/woff/GeneralSans-Bold.woff',
            woff2: '/fonts/woff2/GeneralSans-Bold.woff2',
          },
        },
        italic: {
          name: 'GeneralSans-Italic',
          weight: 400,
          style: 'italic',
          files: {
            woff: '/fonts/woff/GeneralSans-Italic.woff',
            woff2: '/fonts/woff2/GeneralSans-Italic.woff2',
          },
        },
        semiboldItalic: {
          name: 'GeneralSans-SemiboldItalic',
          weight: 600,
          style: 'italic',
          files: {
            woff: '/fonts/woff/GeneralSans-SemiboldItalic.woff',
            woff2: '/fonts/woff2/GeneralSans-SemiboldItalic.woff2',
          },
        },
      },
    },
  },
  fontSizes: {
    xs: '12px',
    sm: '14px',
    md: '16px',
    lg: '18px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '30px',
    '4xl': '36px',
    '5xl': '48px',
    '6xl': '60px',
    '7xl': '72px',
    '8xl': '96px',
    '9xl': '128px',
  },
  fontWeights: {
    thin: '100',
    extralight: '200',
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
    black: '900',
  },
  lineHeights: {
    '3': '12px',
    '4': '16px',
    '5': '20px',
    '6': '24px',
    '7': '28px',
    '8': '32px',
    '9': '36px',
    '10': '40px',
    none: '1',
    tight: '1.25',
    snug: '1.375',
    normal: '1.5',
    relaxed: '1.625',
    loose: '2',
  },
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },
} as const

export const semantic = {
  button: {
    primary: {
      bg: {
        default: '#EF476F',
        hover: '#F69CB1',
      },
      fg: {
        default: '#2F2B3A',
      },
    },
  },
} as const

// Unified token export
export const tokens = {
  color,
  typography,
  semantic,
} as const

export default tokens

// Type exports for TypeScript support
export type Tokens = typeof tokens
export type ColorTokens = typeof color
export type TypographyTokens = typeof typography
export type SemanticTokens = typeof semantic
