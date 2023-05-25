const path = require("path");
const CopyPlugin = require("copy-webpack-plugin");

module.exports = {
  // Entry files for our webapp
  entry: {
    webapp: "./webapp/Configure.tsx",
  },
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'dist'),
    //path: path.resolve(__dirname, "..", "extension"),
  },
  mode: "production",

  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: [
          {
            loader: "ts-loader",
            options: {
              compilerOptions: { noEmit: false },
            },
          },
        ],
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: [".tsx", ".ts", ".js"],
  },

  plugins: [

    // copy extension manifest and icons
    new CopyPlugin({
      patterns: [
        // {
        //   from: './src/',
        //   globOptions: {
        //     ignore: ['**/__pycache__']
        //   }
        // },
        {
          context: './webapp/assets/',
          from: '*.png',
          to: 'assets/'
        }
      ]
    }),
  ],
};