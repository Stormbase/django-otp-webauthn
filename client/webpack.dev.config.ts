import { Configuration } from "webpack";
import { merge } from "webpack-merge";

import baseConfig from "./webpack.base.config";

const config: Configuration = {
  mode: "development",
  devtool: "inline-source-map",
};

export default merge(baseConfig, config);
