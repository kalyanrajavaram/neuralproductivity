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
  const [recordSession, setRecordSession] = useState(false); // NEW STATE
  const intervalRef = useRef(null);

  // Webcam + Recording Refs
  const videoRef = useRef(null);
  const recorderRef = useRef(null);
  const [chunks, setChunks] = useState([]);

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

  // Format time nicely
  const formatTime = (seconds) => {
    const min = Math.floor(seconds / 60).toString().padStart(2, '0');
    const sec = (seconds % 60).toString().padStart(2, '0');
    return `${min}:${sec}`;
  };

  // ========================
  // Webcam Setup + Recording
  // ========================
  useEffect(() => {
    async function setupWebcam() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        videoRef.current.srcObject = stream;

        const recorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) {
            setChunks((prev) => [...prev, e.data]);
          }
        };

        recorderRef.current = recorder;
      } catch (err) {
        console.error('Error accessing webcam:', err);
      }
    }
    setupWebcam();
  }, []);

  // Auto-upload the recorded session to backend
  const uploadVideo = async () => {
    if (!recordSession || chunks.length === 0) return; // Skip if not recording

    const blob = new Blob(chunks, { type: 'video/webm' });
    setChunks([]); // clear after upload

    const formData = new FormData();
    formData.append('video', blob, 'study_session.webm');

    try {
      await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
      console.log('Video uploaded successfully!');
    } catch (err) {
      console.error('Error uploading video:', err);
    }
  };

  // ========================
  // Pomodoro Timer Logic
  // ========================
  const handleStart = () => {
    if (isRunning) return;
    setIsRunning(true);

    // Start recording ONLY if toggle is ON
    if (recordSession && recorderRef.current && recorderRef.current.state === 'inactive') {
      setChunks([]);
      recorderRef.current.start();
      console.log('Recording started...');
    }

    intervalRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev === 0) {
          clearInterval(intervalRef.current);
          setIsRunning(false);

          // Stop recording automatically when session ends
          if (recordSession && recorderRef.current && recorderRef.current.state === 'recording') {
            recorderRef.current.stop();
            console.log('Recording stopped...');
            recorderRef.current.onstop = uploadVideo;
          }

          // Switch to next mode
          setMode((prevMode) => {
            if (prevMode === 'focus') return 'shortBreak';
            else if (prevMode === 'shortBreak') return 'longBreak';
            else return 'focus';
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

    if (recordSession && recorderRef.current && recorderRef.current.state === 'recording') {
      recorderRef.current.stop();
      console.log('Recording stopped due to pause...');
      recorderRef.current.onstop = uploadVideo;
    }
  };

  const handleReset = () => {
    clearInterval(intervalRef.current);
    setIsRunning(false);
    setSecondsLeft(modeSettings[mode].duration);

    if (recordSession && recorderRef.current && recorderRef.current.state === 'recording') {
      recorderRef.current.stop();
      console.log('Recording stopped due to reset...');
      recorderRef.current.onstop = uploadVideo;
    }
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

        {/* Live Webcam Preview */}
        {recordSession && (
          <video ref={videoRef} autoPlay playsInline style={{ width: '400px', borderRadius: '8px' }} />
        )}

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

        {/* Start / Pause / Reset */}
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

        {/* Mode Switching */}
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

        {/* NEW BUTTON TO TOGGLE RECORDING */}
        <Button
          size="lg"
          colorScheme={recordSession ? 'pink' : 'gray'}
          variant={recordSession ? 'solid' : 'outline'}
          onClick={() => setRecordSession((prev) => !prev)}
        >
          {recordSession ? 'Recording Enabled ✅' : 'Record Session 🎥'}
        </Button>
      </VStack>
    </Box>
  );
}

export default PomodoroTimer;
