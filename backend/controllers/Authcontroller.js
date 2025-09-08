const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const UserModel = require('../models/user');

const Signup = async (req, res) => {
   try{
    const { name, email, password } = req.body;
    const user = await UserModel.findOne({ email: email });
    if (user) {
        return res.status(409).json({ message: 'User already exists', success: false });
    }
    const userModel = new UserModel({ name, email, password });
    userModel.password = await bcrypt.hash(password, 10);
    await userModel.save();
    res.status(201).json({ message: 'User created successfully', success: true });
   }
   catch(err){
    console.log("Signup error",err);
    res.status(500).json({ message: 'Internal Server Error', success: false });
   }
}
const login = async (req, res) => {
   try{
    const {email, password } = req.body;
    const user = await UserModel.findOne({ email});
    const errorMessage = 'Invalid email or password';
    if (!user) {
        return res.status(409).json({ message: errorMessage, success: false });
    }
    
    const isPasswordValid = await bcrypt.compare(password, user.password);
    if (!isPasswordValid) {
        return res.status(403)
        .json({ message: errorMessage, success: false });
    }

    const token = jwt.sign(
        { email: user.email , _id: user._id }, 
        process.env.JWT_SECRET,
         { expiresIn: '24h' }
    )

    res.status(200)
    .json({
        message: 'Login successful',
        success: true,
        token,
        email,
        name: user.name
     });
   }
   catch(err){
    console.log("Login error",err);
    res.status(500)
    .json({ message: 'Internal Server Error', 
            success: false });
   }
}
module.exports = {
    Signup,
    login
 };