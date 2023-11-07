/*
  Configuration UI for tana-helper

  Built as a React app
*/

import React from "react";
import { createRoot } from "react-dom/client";
// import reportWebVitals from "./reportWebVitals";
import ConfigurationPanel from "./ConfigurationPanel";

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error('Failed to find the root element');

const root = createRoot(rootElement);
root.render(
  <React.StrictMode>
    <ConfigurationPanel />
  </React.StrictMode>
);

// reportWebVitals();