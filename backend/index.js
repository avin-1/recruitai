require('dotenv').config();

const express = require('express');
const app = express();

const bodyParser = require('body-parser');
const cors = require('cors');
const authRouter = require('./routes/authRouter');

const PORT = process.env.PORT || 3000;
require('./models/db');

app.use(bodyParser.json());
app.use(cors());
app.use('/auth', authRouter);

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

app.get('/', (req, res) => {
    res.send('Hello World!');
});