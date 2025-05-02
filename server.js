require('dotenv').config();
const express = require('express');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');

const app = express();
const upload = multer({ dest: 'uploads/' });

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  }
});

app.use(express.static('public'));

app.post('/upload', upload.single('image'), async (req, res) => {
  const file = req.file;
  const ext = path.extname(file.originalname);
  const key = `uploads/${Date.now()}${ext}`;
  const fileContent = fs.readFileSync(file.path);

  const params = {
    Bucket: process.env.S3_BUCKET,
    Key: key,
    Body: fileContent,
    ContentType: file.mimetype,
    ACL: 'public-read'
  };

  try {
    await s3.send(new PutObjectCommand(params));
    fs.unlinkSync(file.path); // cleanup
    res.redirect('/result.html');
  } catch (err) {
    console.error(err);
    res.status(500).send('Failed to upload');
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
