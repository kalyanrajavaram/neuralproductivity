import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Text,
  Button,
  VStack,
  HStack,
  Heading,
  Circle,
  useColorModeValue,
} from '@chakra-ui/react';

function PomodoroTimer() {
  const [mode, setMode] = useState('focus'); 
  const [secondsLeft, setSecondsLeft] = useState(25 * 60);
  const [isRunning, setIsRunning] = useState(false);
  const intervalRef = useRef(null);

  // Map modes to name, color, and time
  const modeSettings = {
    focus: {
      label: 'Focus Time',
      duration: 25 * 60,
      color: 'blue.300',
    },
    shortBreak: {
      label: 'Short Break',
      duration: 5 * 60,
      color: 'green.300',
    },
    longBreak: {
      label: 'Long Break',
      duration: 15 * 60,
      color: 'purple.300',
    },
  };

  const formatTime = (seconds) => {
    const min = Math.floor(seconds / 60).toString().padStart(2, '0');
    const sec = (seconds % 60).toString().padStart(2, '0');
    return `${min}:${sec}`;
  };

  const handleStart = () => {
    if (isRunning) return;
    setIsRunning(true);

    intervalRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev === 0) {
          clearInterval(intervalRef.current);
          setIsRunning(false);
          setMode((prevMode) => {
            if (prevMode === 'focus') {
              return 'shortBreak';
            } else if (prevMode === 'shortBreak') {
              return 'longBreak';
            } else {
              return 'focus';
            }
          });
          return modeSettings[mode].duration; 
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handlePause = () => {
    clearInterval(intervalRef.current);
    setIsRunning(false);
  };

  const handleReset = () => {
    clearInterval(intervalRef.current);
    setIsRunning(false);
    setSecondsLeft(modeSettings[mode].duration);
  };

  const handleModeChange = (newMode) => {
    clearInterval(intervalRef.current);
    setIsRunning(false);
    setMode(newMode);
    setSecondsLeft(modeSettings[newMode].duration);
  };

  useEffect(() => {
    return () => clearInterval(intervalRef.current);
  }, []);

  const bg = useColorModeValue(modeSettings[mode].color, modeSettings[mode].color);

  return (
    <Box bg={bg} minH="100vh" display="flex" alignItems="center" justifyContent="center" px={4}>
      <VStack spacing={10}>
        <Heading size="xl" textAlign="center">
          {modeSettings[mode].label}
        </Heading>

        <Circle
          size="300px"
          border="12px solid"
          borderColor="teal.400"
          boxShadow="0 0 40px rgba(0, 128, 128, 0.5)"
          display="flex"
          alignItems="center"
          justifyContent="center"
        >
          <Text fontSize="6xl" fontWeight="semibold">
            {formatTime(secondsLeft)}
          </Text>
        </Circle>

        <HStack spacing={6}>
          <Button size="lg" colorScheme="green" onClick={handleStart}>
            Start
          </Button>
          <Button size="lg" colorScheme="orange" onClick={handlePause}>
            Pause
          </Button>
          <Button size="lg" colorScheme="red" variant="outline" onClick={handleReset}>
            Reset
          </Button>
        </HStack>

        <HStack spacing={4}>
          <Button onClick={() => handleModeChange('focus')} colorScheme="blue">
            Focus
          </Button>
          <Button onClick={() => handleModeChange('shortBreak')} colorScheme="green">
            Short Break
          </Button>
          <Button onClick={() => handleModeChange('longBreak')} colorScheme="purple">
            Long Break
          </Button>
        </HStack>
      </VStack>
    </Box>
  );
}

export default PomodoroTimer;
