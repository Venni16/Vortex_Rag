const express = require('express');
const axios = require('axios');
const cors = require('cors');
const multer = require('multer');
const FormData = require('form-data');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 5000;
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://ai-service:8000';
const API_KEY = process.env.AI_SERVICE_API_KEY || 'dev-secret-change-me';

app.use(cors());
app.use(express.json());

// Multer for file uploads
const upload = multer({ storage: multer.memoryStorage() });

// ── RAG Chat Gateway ─────────────────────────────────────────────────────────
app.post('/api/chat', async (req, res) => {
  try {
    const { question, collection } = req.body;
    const response = await axios.post(`${AI_SERVICE_URL}/api/v1/query`, {
      question,
      collection: collection || 'default'
    }, {
      headers: { 'x-api-key': API_KEY }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Chat Error:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
  }
});

// ── Document Ingestion Gateway ───────────────────────────────────────────────
app.post('/api/ingest/file', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: 'No file uploaded' });

    const form = new FormData();
    form.append('file', req.file.buffer, {
      filename: req.file.originalname,
      contentType: req.file.mimetype,
    });
    if (req.body.collection) form.append('collection', req.body.collection);

    const response = await axios.post(`${AI_SERVICE_URL}/api/v1/upload/doc`, form, {
      headers: {
        ...form.getHeaders(),
        'x-api-key': API_KEY
      }
    });
    res.status(202).json(response.data);
  } catch (error) {
    console.error('File Upload Error:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
  }
});

// ── URL Ingestion Gateway ────────────────────────────────────────────────────
app.post('/api/ingest/url', async (req, res) => {
  try {
    const { url, collection, deep_scrape } = req.body;
    const response = await axios.post(`${AI_SERVICE_URL}/api/v1/upload/url`, {
      url,
      collection: collection || 'default',
      deep_scrape: deep_scrape || false
    }, {
      headers: { 'x-api-key': API_KEY }
    });
    res.status(202).json(response.data);
  } catch (error) {
    console.error('URL Ingestion Error:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
  }
});

// ── Job Status Polling ────────────────────────────────────────────────────────
app.get('/api/ingest/status/:jobId', async (req, res) => {
  try {
    const response = await axios.get(`${AI_SERVICE_URL}/api/v1/upload/status/${req.params.jobId}`);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
  }
});

// ── Health Check ─────────────────────────────────────────────────────────────
app.get('/health', (req, res) => res.json({ status: 'ok', service: 'Backend Gateway' }));

app.listen(port, () => {
  console.log(`Vortex Backend Gateway running on port ${port}`);
  console.log(`Connected to AI Service at ${AI_SERVICE_URL}`);
});
