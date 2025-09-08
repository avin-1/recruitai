
const { signupValidation, loginValidation } = require('../middlewares/AuthValidation');
const { Signup, login } = require('../controllers/Authcontroller');


const router = require('express').Router();

router.post('/login', loginValidation, login);
router.post('/signup', signupValidation, Signup);

module.exports = router;