const request = require('supertest');

// Import your app or define it here for test
const app = require('./app');

describe('GET /', () => {
  it('should return Hello from ECS Fargate v2', async () => {
    const res = await request(app).get('/');
    expect(res.statusCode).toBe(200);
    expect(res.text).toBe('Hello from ECS Fargate v2');
  });
});
