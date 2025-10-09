const { composePlugins, withNx } = require('@nx/webpack');
const webpack = require('webpack');

module.exports = composePlugins(withNx(), (config) => {
  // Fix for ES module directory imports
  config.output = config.output || {};
  config.output.module = false;
  config.output.libraryTarget = 'commonjs2';
  config.output.chunkFormat = 'commonjs';

  // Ensure proper module resolution
  config.resolve = config.resolve || {};
  config.resolve.fullySpecified = false;

  // Add extensions to resolve
  config.resolve.extensions = ['.ts', '.tsx', '.mjs', '.js', '.jsx', '.json'];

  const optionalModules = [
    '@nestjs/microservices/microservices-module',
    '@nestjs/microservices',
    '@nestjs/websockets/socket-module',
    'class-transformer/storage',
    '@mikro-orm/core',
    '@nestjs/sequelize/dist/common/sequelize.utils',
    '@nestjs/typeorm/dist/common/typeorm.utils',
    '@mapbox/node-pre-gyp',
    '@mongodb-js/zstd',
    '@aws-sdk/credential-providers',
    'gcp-metadata',
    'snappy',
    'socks',
    'aws4',
    'mongodb-client-encryption',
    'mock-aws-s3',
    'aws-sdk',
    'nock',
    'node-gyp',
    'npm',
    'kerberos',
  ];

  config.resolve.alias = {
    ...(config.resolve.alias || {}),
  };

  optionalModules.forEach((moduleName) => {
    if (typeof config.resolve.alias[moduleName] === 'undefined') {
      config.resolve.alias[moduleName] = false;
    }
  });

  config.plugins = config.plugins || [];
  config.plugins.push(
    new webpack.IgnorePlugin({ resourceRegExp: /\.d\.ts$/ }),
    new webpack.IgnorePlugin({ resourceRegExp: /\.js\.map$/ }),
    new webpack.IgnorePlugin({ resourceRegExp: /\.html$/, contextRegExp: /@mapbox\/node-pre-gyp/ }),
    new webpack.NormalModuleReplacementPlugin(/\.d\.ts$/, (resource) => {
      resource.request = resource.request.replace(/\.d\.ts$/, '.js');
    }),
  );

  // Set experiments to disable ES modules
  config.experiments = config.experiments || {};
  config.experiments.outputModule = false;

  // CRITICAL: Force bundling of @draft-genie/* libs
  // Override externals completely to ensure libs are bundled
  config.externals = [];

  return config;
});
