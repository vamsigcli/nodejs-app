const express = require('express');
const app = express();

// Health check endpoint — returns 200 so ECS deployment succeeds
// Circuit breaker only checks this, so deployment will complete successfully
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

// Main route — returns 200 with a greeting message
app.get('/', (req, res) => {
  res.send('Hello from ECS Fargate v2');
});

if (require.main === module) {
  app.listen(3000, '0.0.0.0', () => {
    console.log('App running on port 3000');
  });
}

module.exports = app;
