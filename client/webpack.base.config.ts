import path from "path";
import { Configuration } from "webpack";

const config: Configuration = {
  stats: "minimal",
  entry: {
    auth: "./client/src/auth.ts",
    register: "./client/src/register.ts",
  },
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: "ts-loader",
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: [".ts", ".js"],
  },
  output: {
    filename: "otp_webauthn_[name].js",
    path: path.resolve("./src/django_otp_webauthn/static/django_otp_webauthn"),
  },
};

export default config;
