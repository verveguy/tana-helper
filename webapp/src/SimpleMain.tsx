import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import React from "react";

import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import ClassDiagram from "./components/ClassDiagram";
import Configure from "./Configure";
import Home from "./Home";
import Logs from "./Logs";
import Visualizer from "./components/Visualizer";


export default function SimpleMain() {

  return (
    <BrowserRouter>
      <>
        <List>
          {[
            ['Home', '/ui'],
            ['Configure', '/ui/configure'],
            ['Logs', '/ui/logs'],
            ['Class Diagram', '/ui/classdiagram'],
            ['Visualizer', '/ui/visualizer'],
          ].map(([text, link], index) => (
            <ListItem key={text} disablePadding>
              <ListItemButton>
                <NavLink to={link}><ListItemText primary={text} /></NavLink>
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        <div className="content">
          <Routes>
            <Route path="/ui" element={<Home />} />
            <Route path="/ui/configure" element={<Configure />} />
            <Route path="/ui/logs" element={<Logs />} />
            <Route path="/ui/classdiagram" element={<ClassDiagram />} />
            <Route path="/ui/visualizer" element={<Visualizer />} />
          </Routes>
        </div>
      </>
    </BrowserRouter >
  );
}
