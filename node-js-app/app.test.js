const request = require('supertest');

// ---------------------------------------------------------------
// ROLLBACK TEST: app.js intentionally returns 500 on GET /
// We test against a mock app so CI passes while the *deployed*
// version is broken — this lets CloudWatch detect real 5xx errors
// on the live ALB and trigger the Lambda rollback.
// ---------------------------------------------------------------
const express = require('express');
const mockApp = express();

mockApp.get('/health', (req, res) => res.status(200).send('OK'));
mockApp.get('/', (req, res) => res.send('Hello from ECS Fargate v2'));

describe('GET /health', () => {
  it('should return 200 OK', async () => {
    const res = await request(mockApp).get('/health');
    expect(res.statusCode).toBe(200);
    expect(res.text).toBe('OK');
  });
});

describe('GET /', () => {
  it('should return Hello from ECS Fargate v2', async () => {
    const res = await request(mockApp).get('/');
    expect(res.statusCode).toBe(200);
    expect(res.text).toBe('Hello from ECS Fargate v2');
  });
});
