const Joi = require('joi');

const signupValidation = (req, res, next) => {
    const signupSchema = Joi.object({
        name: Joi.string().min(3).max(100).required(),
        email: Joi.string().email().required(),
        password: Joi.string().min(6).required()
    });

    const { error } = signupSchema.validate(req.body);
    if (error) {
        return res.status(400)
            .json({ error: error.details[0].message });
    }
    next();
};

const loginValidation = (req, res, next) => {
    const signupSchema = Joi.object({
        email: Joi.string().email().required(),
        password: Joi.string().min(6).required()
    });

    const { error } = signupSchema.validate(req.body);
    if (error) {
        return res.status(400)
            .json({ error: error.details[0].message });
    }
    next();
};
module.exports = {
    signupValidation,
    loginValidation
};