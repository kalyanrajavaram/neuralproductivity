// App.jsx
import { ChakraProvider } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Home from './pages/Home';
import Preferences from './pages/Preferences';
import Dashboard from './pages/Dashboard';
import PomodoroTimer from './components/PomodoroTimer';


function App() {
  return (
    <ChakraProvider >
      <Router>
        <Routes>
          <Route path="/" element={<Home/>} />
          <Route path="/dashboard" element={<Dashboard />} />`
          <Route path="/preferences" element={<Preferences /> }/> 
          <Route path="/timer" element={<PomodoroTimer />} />
        </Routes>
      </Router>
    </ChakraProvider>
  );
}

export default App;
