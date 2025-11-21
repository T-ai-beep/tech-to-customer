import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Disabled because the community package `babel-plugin-react-compiler` is not available
  // during create-next-app; enabling this will make Next try to resolve that package.
  reactCompiler: false,
};

export default nextConfig;
