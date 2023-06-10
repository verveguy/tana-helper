import { ThemeProvider, createTheme } from '@mui/material/styles';
import GraphWorkspace from './GraphWorkspace';

// use emotion for CSS when ready
// https://emotion.sh/docs/introduction

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

function GraphApp() {
  return (
    <ThemeProvider theme={darkTheme}>
      <GraphWorkspace />
    </ThemeProvider>
  );
}

export default GraphApp;