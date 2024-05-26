import { Configuration } from "webpack";
import { merge } from "webpack-merge";
import TerserPlugin from "terser-webpack-plugin";

import baseConfig from "./webpack.base.config";

const config: Configuration = {
  mode: "production",
  devtool: "source-map",
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        minify: TerserPlugin.esbuildMinify,
      }),
    ],
  },
  output: {
    clean: true,
  }
};

export default merge(baseConfig, config);
