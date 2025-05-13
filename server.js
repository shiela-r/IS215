require('dotenv').config();

const express = require('express');
require('dotenv').config();

const multer = require('multer');
const fs = require('fs');
const path = require('path');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');

const app = express();
const upload = multer({ dest: 'uploads/' });
console.log('Access Key:', process.env.AWS_ACCESS_KEY_ID);

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    sessionToken: process.env.AWS_SESSION_TOKEN 
  }
});

app.use(express.static('public'));

app.post('/upload', upload.single('image'), async (req, res) => {
  const file = req.file;

  if (!file) {
    console.error('? No file was uploaded.');
    return res.status(400).send('No file uploaded.');
  }

  const filePath = file.path;
  const key = `uploads/${Date.now()}_${file.originalname}`;

  const params = {
    Bucket: process.env.S3_BUCKET_NAME,
    Key: key,
    Body: fs.readFileSync(filePath),
    ContentType: file.mimetype
  };

  try {
    console.log(`?? Uploading ${file.originalname} to S3 as ${key}...`);
    const result = await s3.send(new PutObjectCommand(params));
    console.log('? Upload successful:', result);

    fs.unlinkSync(filePath); // Delete local temp file
    res.redirect('/result.html');

  } catch (error) {
    console.error('? S3 Upload Failed');
    console.error('Error Code:', error.name || 'N/A');
    console.error('Message:', error.message || 'No message provided');
    console.error('Stack:', error.stack || 'No stack trace');
    res.status(500).send(`Upload failed: ${error.message}`);
  }
});

app.listen(3000, '0.0.0.0', () => {
  console.log('?? Server running on port 3000 and listening on 0.0.0.0');
});
