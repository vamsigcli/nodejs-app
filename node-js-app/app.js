const express = require('express');
const app = express();

// Health check endpoint — returns 200 so ECS deployment succeeds
// Circuit breaker only checks this, so deployment will complete successfully
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

// TEMP: Main route intentionally returns 500 to simulate a runtime bug
// This will NOT be caught by the circuit breaker (deployment succeeds)
// but WILL trigger the CloudWatch ALB 5xx alarm → Lambda rollback
app.get('/', (req, res) => {
  res.status(500).json({
    error: 'Internal Server Error',
    message: 'TEMP: Intentional 500 to test CloudWatch alarm → Lambda rollback',
  });
});

if (require.main === module) {
  app.listen(3000, '0.0.0.0', () => {
    console.log('App running on port 3000');
  });
}

module.exports = app;
