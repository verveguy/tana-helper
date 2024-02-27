/*
  Log Viewer UI for tana-helper

  Built as a React app
*/
import React from 'react';
import { createRoot } from "react-dom/client";
import App from './App';
import './Root.css';

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error('Failed to find the root element');

const root = createRoot(rootElement);

root.render(
  // <StrictMode>
    <App />
  // </StrictMode>
);
