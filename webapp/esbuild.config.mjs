import { copy } from 'esbuild-plugin-copy';
import { build } from 'esbuild'

const res = await build({
  entryPoints: [
    'src/Root.tsx',
  ],

  platform: 'browser',
  bundle: true,
  // minify: true,
  minify: false,
  format: 'iife',
  write: true,
  sourcemap: true,
  outdir: './dist',
  jsx: 'automatic',
  jsxDev: true,
  // external: ['react', 'react-dom'],
  plugins: [
    copy({
      // this is equal to process.cwd(), which means we use cwd path as base path to resolve `to` path
      // if not specified, this plugin uses ESBuild.build outdir/outfile options as base path.
      resolveFrom: 'cwd',
      assets: {
        from: ['./assets/**/*'],
        to: ['./dist/assets/'],
      }
    }),
    copy({
      // this is equal to process.cwd(), which means we use cwd path as base path to resolve `to` path
      // if not specified, this plugin uses ESBuild.build outdir/outfile options as base path.
      resolveFrom: 'cwd',
      assets: {
        from: ['./templates/**/*'],
        to: ['./dist/templates/'],
      },
    }),
  ]
})

