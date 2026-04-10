const express = require('express');
const app = express();

app.get('/', (req, res) => { // eslint-disable-line no-unused-vars
  // TEMP: Intentional crash to test ECS deployment circuit breaker rollback
  // Remove this block and restore the original response after rollback is verified
  console.error('Intentional failure for ECS rollback test');
  process.exit(1);
});

if (require.main === module) {
  app.listen(3000, '0.0.0.0', () => {
    console.log('App running on port 3000');
  });
}

module.exports = app;
