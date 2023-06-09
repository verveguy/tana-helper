import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import GraphWorkspace from './GraphWorkspace';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

function GraphApp() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <GraphWorkspace />
    </ThemeProvider>
  );
}

export default GraphApp;