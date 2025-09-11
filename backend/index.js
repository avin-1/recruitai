require('dotenv').config();

const express = require('express');
const cors = require('cors');
const authRouter = require('./routes/auth');
require('./models/db'); // connect DB

const app = express();
const PORT = process.env.PORT || 5000;

// Middlewares
app.use(express.json());
app.use(cors()); // you can restrict origin: app.use(cors({ origin: 'http://localhost:3000' }))

// Routes
app.use('/api/auth', authRouter);

// simple test
app.get('/', (req, res) => res.send('Hello from RecruitAI backend'));

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
