throw new Error("Intentional failure for rollback test");

const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.send('Hello from ECS Fargate v2');
});

if (require.main === module) {
  app.listen(3000, '0.0.0.0', () => {
    console.log('App running on port 3000');
  });
}

module.exports = app;
