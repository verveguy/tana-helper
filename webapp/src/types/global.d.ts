// Global type declarations
/// <reference types="react" />

// Custom elements
declare namespace JSX {
  interface IntrinsicElements {
    'rapi-doc': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
      'spec-url'?: string;
    };
  }
}

// All major packages now have proper TypeScript support!
// Only custom elements and Vite-specific declarations remain here.

// Vite environment variables
interface ImportMetaEnv {
  readonly DEV: boolean;
  readonly PROD: boolean;
  readonly MODE: string;
  // Add other env variables as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
  readonly hot?: {
    accept(): void;
    accept(cb: () => void): void;
    accept(dep: string, cb: () => void): void;
    accept(deps: string[], cb: () => void): void;
  };
}
