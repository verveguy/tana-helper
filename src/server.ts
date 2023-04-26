/*
  Core server for handling HTTP requests as a localservice
  and accepting CORS requests from app.tana.inc 

  Provides GET / endpoint for liveness testing and
  POST /log endpoint for debugging support
*/

import express, { NextFunction, Request, Response } from "express";
import bodyParser from "body-parser";
import { config as dotenvConfig } from 'dotenv';
import cors from 'cors';
import helmet from 'helmet';
import winston from "winston";
import expressWinston from 'express-winston';

console.log("Loading server");

// read .env to get our API keys
dotenvConfig();

const LOCAL_SERVICE = (process.env.LOCAL_SERVICE ?? true) as boolean;
const PORT = (process.env.PORT ?? 4000) as number;

// Localservice operation is configured differently. Notify such.
if (LOCAL_SERVICE) {
  console.log('Running as local service. No authentication required.');
}

// create our web server
export const app = express();

// turn on logging via winston
// more options here - https://github.com/bithavoc/express-winston#request-logging
app.use(expressWinston.logger({
  transports: [
    new winston.transports.Console()
  ],
  format: winston.format.combine(
    winston.format.colorize(),
    winston.format.json()
  ),
  meta: false,
  msg: "HTTP  ",
  expressFormat: true,
  colorize: false,
  ignoreRoute: function (req, res) { return false; }
}));

// API security middleware
app.use(helmet());

// Configure CORS for localhost access
const corsOptions = {
  origin: 'https://app.tana.inc',
  methods: ['GET', 'POST'],
};

// activate CORS middleware
app.use(cors(corsOptions));

// assume JSON in all cases
app.use(bodyParser.json({ type: ['text/plain', 'application/json'] }));

//app.use(bodyParser.text({ type: 'text/plain' }));

// Middleware to accept only connections from localhost
// app.use((req:Request, res:Response, next: NextFunction) => {
//   if (req.hostname === 'localhost' || req.hostname === '127.0.0.1') {
//     next();
//   } else {
//     res.status(403).send('Forbidden');
//   }
// });

// unauthenticated health check endpoint
// keeps Vercel happy. Declare this before 
// adding 
app.get('/', (req: Request, res: Response) => {
  res.send({ success: true, message: "It is working" });
});

export const baseUrl = `http://localhost:${PORT}`;

// LOG so we can see the data in the log
app.post('/log', async (req: Request, res: Response) => {
  console.log(req.body);
  res.status(200).send();
});

app.listen(PORT, 'localhost', () => {
  console.log(`Server is listening on http://localhost:${PORT}`);
});

export default app;



