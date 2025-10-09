const { composePlugins, withNx } = require('@nx/webpack');
const webpack = require('webpack');

module.exports = composePlugins(withNx(), (config) => {
  config.resolve = config.resolve || {};
  config.resolve.fullySpecified = false;
  config.resolve.extensions = ['.ts', '.tsx', '.mjs', '.js', '.jsx', '.json'];

  // Exclude .d.ts files from module resolution
  config.resolve.extensionAlias = {
    '.d.ts': false,
  };

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

  // Exclude .d.ts files from being processed
  config.module = config.module || {};
  config.module.rules = config.module.rules || [];

  // Add rule to handle .d.ts files - place it at the beginning to take precedence
  config.module.rules.unshift({
    test: /\.d\.ts$/,
    use: 'null-loader',
  });

  config.plugins = config.plugins || [];
  config.plugins.push(
    new webpack.IgnorePlugin({ resourceRegExp: /\.d\.ts$/ }),
    new webpack.IgnorePlugin({ resourceRegExp: /\.js\.map$/ }),
    new webpack.IgnorePlugin({ resourceRegExp: /\.html$/, contextRegExp: /@mapbox\/node-pre-gyp/ }),
  );

  // Fix for ES module directory imports - force bundling of @draft-genie/* libs
  config.output = config.output || {};
  config.output.module = false;
  config.output.libraryTarget = 'commonjs2';
  config.output.chunkFormat = 'commonjs';

  // CRITICAL: Force bundling of @draft-genie/* libs, but keep @nestjs/terminus external
  config.externals = [
    function ({ request }, callback) {
      // Keep @nestjs/terminus external to avoid .d.ts bundling issues
      if (request && request.startsWith('@nestjs/terminus')) {
        return callback(null, 'commonjs ' + request);
      }
      callback();
    },
  ];

  return config;
});
