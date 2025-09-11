const mongoose = require('mongoose');

const mongo_uri = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/recruitai';

mongoose
  .connect(mongo_uri, {
    // options are fine with current mongoose versions
  })
  .then(() => console.log('✅ MongoDB connected'))
  .catch((err) => {
    console.error('❌ MongoDB connection error:', err.message);
    process.exit(1);
  });
