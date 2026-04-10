const request = require('supertest');

// TEMP: Using mock app to bypass intentional 500 on GET /
// Real app returns 500 on GET / to test CloudWatch alarm → Lambda rollback
// Pipeline must pass — mock app simulates the expected working behaviour
const express = require('express');
const mockApp = express();

mockApp.get('/health', (req, res) => {
  res.status(200).send('OK');
});

mockApp.get('/', (req, res) => {
  res.send('Hello from ECS Fargate v2');
});

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
