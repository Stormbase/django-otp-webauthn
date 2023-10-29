import { defineConfig } from "vite";
import path from "path";

export default defineConfig({
  build: {
    minify: false,
    outDir: path.resolve("../otp_passkeys/static/otp_passkeys"),
    emptyOutDir: true,
    lib: {
      entry: {
        otp_passkeys_auth: "./src/auth.ts",
        otp_passkeys_register: "./src/register.ts",
      },
    },
  },
});
