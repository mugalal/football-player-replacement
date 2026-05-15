/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Player photo and team logo URLs come from the backend's /static/ mount.
  // We don't use next/image's optimization for those; the backend returns
  // absolute URLs and we render them via plain <img>. So no `images.domains`
  // config is required.
};

module.exports = nextConfig;
