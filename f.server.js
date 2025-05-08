require('dotenv').config();
const express = require('express');
const multer = require('multer');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const path = require('path');

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

const {
  AWS_ACCESS_KEY_ID,
  AWS_SECRET_ACCESS_KEY,
  AWS_SESSION_TOKEN,
  AWS_REGION,
  S3_BUCKET_NAME
} = process.env;

const s3 = new S3Client({
  region: AWS_REGION,
  credentials: {
    accessKeyId: AWS_ACCESS_KEY_ID,
    secretAccessKey: AWS_SECRET_ACCESS_KEY,
    sessionToken: AWS_SESSION_TOKEN,
  }
});

// Serve static files from 'public' directory (e.g., index.html, result.html)
app.use(express.static(path.join(__dirname, 'public')));

// Serve index.html as homepage
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Upload handler
app.post('/upload', upload.single('image'), async (req, res) => {
  const file = req.file;
  if (!file) {
    return res.status(400).send('No file uploaded.');
  }

  const key = `uploads/${Date.now()}_${file.originalname}`;

  try {
    await s3.send(new PutObjectCommand({
      Bucket: S3_BUCKET_NAME,
      Key: key,
      Body: file.buffer,
      ContentType: file.mimetype,
    }));

    console.log('? Upload success:', key);
    return res.redirect(`/result.html?key=${encodeURIComponent(key)}`);
  } catch (err) {
    console.error('? Upload error:', err);
    res.status(500).send('Upload failed.');
  }
});

// Catch-all fallback
app.get('*', (req, res) => {
  res.status(404).send('404 - Page not found');
});

// Start server
app.listen(3000, '0.0.0.0', () => {
  console.log('? Server running on port 3000');
});
