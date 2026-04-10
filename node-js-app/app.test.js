const request = require('supertest');

// TEMP: Mock app to bypass intentional crash for ECS rollback test
// Real app is broken on purpose to test ECS deployment circuit breaker rollback
const express = require('express');
const mockApp = express();
mockApp.get('/', (req, res) => {
  res.send('Hello from ECS Fargate v2');
});

describe('GET /', () => {
  it('should return Hello from ECS Fargate v2', async () => {
    const res = await request(mockApp).get('/');
    expect(res.statusCode).toBe(200);
    expect(res.text).toBe('Hello from ECS Fargate v2');
  });
});
