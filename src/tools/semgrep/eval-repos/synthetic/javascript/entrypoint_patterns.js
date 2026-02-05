/**
 * Test file for Elttam entrypoint discovery patterns.
 * Contains Express, Koa, and NestJS entrypoint patterns.
 */

const express = require('express');
const app = express();

// ENTRYPOINT_DISCOVERY: Express route
app.get('/', (req, res) => {
    res.json({ message: 'Home page' });
});

// ENTRYPOINT_DISCOVERY: Express route with parameter
app.get('/api/users/:id', (req, res) => {
    res.json({ id: req.params.id });
});

// ENTRYPOINT_DISCOVERY: Express POST route
app.post('/api/users', (req, res) => {
    res.json({ created: true, user: req.body });
});

// ENTRYPOINT_DISCOVERY: Express PUT route
app.put('/api/users/:id', (req, res) => {
    res.json({ updated: true, id: req.params.id });
});

// ENTRYPOINT_DISCOVERY: Express DELETE route
app.delete('/api/users/:id', (req, res) => {
    res.status(204).send();
});

// ENTRYPOINT_DISCOVERY: Express Router
const router = express.Router();

router.get('/products', (req, res) => {
    res.json({ products: [] });
});

router.post('/products', (req, res) => {
    res.json({ created: true });
});

app.use('/api', router);

// ENTRYPOINT_DISCOVERY: Express middleware
app.use('/api/protected', (req, res, next) => {
    // AUDIT_AUTH_CHECK: Authentication middleware
    if (!req.headers.authorization) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
});

// Koa routes (simulated patterns)
// ENTRYPOINT_DISCOVERY: Koa route
const koaHandler = async (ctx) => {
    ctx.body = { message: 'Koa response' };
};

// Fastify routes (simulated patterns)
// ENTRYPOINT_DISCOVERY: Fastify route
const fastifyHandler = async (request, reply) => {
    return { message: 'Fastify response' };
};

// NestJS patterns (simulated)
// ENTRYPOINT_DISCOVERY: NestJS Controller
class UsersController {
    // ENTRYPOINT_DISCOVERY: NestJS route handler
    getAll() {
        return { users: [] };
    }

    // ENTRYPOINT_DISCOVERY: NestJS route with param
    getOne(id) {
        return { user: { id } };
    }

    // ENTRYPOINT_DISCOVERY: NestJS POST handler
    create(createUserDto) {
        return { created: true, user: createUserDto };
    }
}

// AUDIT_INPUT_SINK: User input handling
app.post('/api/process', (req, res) => {
    const userData = req.body; // AUDIT_INPUT_SINK
    res.json({ processed: userData });
});

// AUDIT_FILE_UPLOAD: File upload handling
const multer = require('multer');
const upload = multer({ dest: 'uploads/' });

app.post('/api/upload', upload.single('file'), (req, res) => {
    res.json({ filename: req.file.filename }); // AUDIT_FILE_UPLOAD
});

// AUDIT_SESSION: Session handling
app.get('/api/profile', (req, res) => {
    const session = req.session; // AUDIT_SESSION
    res.json({ user: session.user });
});

module.exports = { app, router, UsersController };
