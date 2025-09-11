const express = require('express');
const bcrypt = require('bcryptjs'); // bcryptjs is pure JS
const jwt = require('jsonwebtoken');
const User = require('../models/user');
const { signupValidation, loginValidation } = require('../middlewares/AuthValidation');

const router = express.Router();

// Signup
router.post('/signup', signupValidation, async (req, res) => {
  try {
    const { name, email, password } = req.body;

    // check if user exists
    const existing = await User.findOne({ email });
    if (existing) return res.status(400).json({ message: 'User already exists' });

    // hash password
    const salt = await bcrypt.genSalt(10);
    const hashed = await bcrypt.hash(password, salt);

    const user = new User({ name, email, password: hashed });
    await user.save();

    return res.status(201).json({ message: 'Account created successfully!' });
  } catch (err) {
    console.error(err);
    // Handle duplicate key error gracefully (just in case race condition)
    if (err.code === 11000) return res.status(400).json({ message: 'Email already in use' });
    return res.status(500).json({ message: 'Server error' });
  }
});

// Login
router.post('/login', loginValidation, async (req, res) => {
  try {
    const { email, password } = req.body;

    const user = await User.findOne({ email });
    if (!user) return res.status(400).json({ message: 'Invalid credentials' });

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(400).json({ message: 'Invalid credentials' });

    const token = jwt.sign({ id: user._id }, process.env.JWT_SECRET, { expiresIn: '1h' });

    return res.json({
      token,
      user: { id: user._id, name: user.name, email: user.email }
    });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;
