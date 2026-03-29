const { createProxyMiddleware } = require('http-proxy-middleware');

const BACKEND_URL = process.env.REACT_APP_BASE_BACKEND_URL || 'http://localhost:9150';

console.log('[setupProxy] Proxying /api -> ' + BACKEND_URL);

module.exports = function (app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: BACKEND_URL,
      changeOrigin: true,
      onError: function (err, req, res) {
        console.error('[proxy] connection error:', err.message);
        res.writeHead(503, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ detail: 'Backend unavailable' }));
      },
    })
  );
};
