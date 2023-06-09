# Tana Graph Visualizer

Inspired by the marketing visualization on the Tana.inc website, `tana-helper` provides a 3D visualization of your Tana workspace.

Check out this [video demo](https://share.cleanshot.com/7J6d6F6l)

## Building

The visualizer UI requires you to build a TypeScript webapp using `yarn`

If you haven't already done so from the instruction on the [top-level README](./README.md), follow these instructions:

Install yarn first, then:

`yarn install`  (downloads all `npm` packages required)

`yarn build` (generates the required `.js` files in `./dist`)

After that, you should be able to hit the url `http://localhost:8000/ui/graph` in your web browser. Use the left sidebar menu to upload your Tana JSON export.

## Notes

The graph visualizer does NOT store your Tana graph on the server when you upload. Instead, every time you change the settings in the visualizer, it re-uploads your graph, the server processes it according to the new settings, and the resulting JSON required for visualization is returned to the browser where it is rendered.

The only state that is kept on the server is your current visualization settings. (This is a temporary workaround)

## Graph processing API

If you're curious, the app POSTs your Tana JSON dump file to the `/graph` endpoint which returns a JSON response consisting of an array of `nodes[]` and `links[]`. These are then rendered by the amazing [3D Force-Directed Graph library](https://github.com/vasturiano/3d-force-graph). YOu can use this endpoint for other experiments of your own.