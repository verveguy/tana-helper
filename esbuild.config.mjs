import { copy } from 'esbuild-plugin-copy';
import { build } from 'esbuild'

const res = await build({
  entryPoints: ['webapp/Graph.tsx', 'webapp/Configure.tsx'],
  platform: 'browser',
  bundle: true,
  minify: true,
  format: 'cjs',
  write: true,
  sourcemap: true,
  outdir: './dist',
  jsx: 'automatic',
  // jsxDev: true,
  // external: ['react', 'react-dom'],
  plugins: [
    copy({
      // this is equal to process.cwd(), which means we use cwd path as base path to resolve `to` path
      // if not specified, this plugin uses ESBuild.build outdir/outfile options as base path.
      resolveFrom: 'cwd',
      assets: {
        from: ['./webapp/assets/**/*'],
        to: ['./dist/assets/'],
      },
    }),
  ] 
})

