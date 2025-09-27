import { useState, useEffect, useRef } from 'react';
import {
  Box, Text, VStack, Heading, Circle, useColorModeValue,
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalCloseButton,
  ModalBody, ModalFooter, Stat, StatLabel, StatNumber, StatHelpText, Divider,
  HStack, Button, Switch, FormControl, FormLabel, Select, Input
} from '@chakra-ui/react';

function PomodoroTimer({ userId = 1 }) {
  const log = (...a) => console.log('[Pomodoro]', ...a);

  // --- state ---
  const [mode, setMode] = useState('focus');
  const [secondsLeft, setSecondsLeft] = useState(25 * 60);
  const [isRunning, setIsRunning] = useState(false);
  const [recordSession, setRecordSession] = useState(false);

  const [isUploading, setIsUploading] = useState(false);
  const [statsOpen, setStatsOpen] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [lastSessionId, setLastSessionId] = useState(null);

  const [task, setTask] = useState('Study Block');
  const [taskCategory, setTaskCategory] = useState('Default');

  // --- refs ---
  const intervalRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const recorderRef = useRef(null);
  const [chunks, setChunks] = useState([]);   // for visibility
  const chunksRef = useRef([]);               // source of truth
  const autoStatsTriggerRef = useRef(null);

  // --- timer config ---
  const modeSettings = {
    focus: { label: 'Focus Time', duration: 25 * 60, color: 'blue.300' },
    shortBreak: { label: 'Short Break', duration: 5 * 60, color: 'green.300' },
    longBreak: { label: 'Long Break', duration: 15 * 60, color: 'purple.300' },
  };
  const formatTime = (s) => `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;
  const getNextMode = (m) => (m === 'focus' ? 'shortBreak' : m === 'shortBreak' ? 'longBreak' : 'focus');
  const switchToNextMode = () => {
    const next = getNextMode(mode);
    log('Mode switch →', mode, '→', next);
    setMode(next);
    setSecondsLeft(modeSettings[next].duration);
  };

  // --- camera helpers ---
  const stopAllTracks = () => {
    try {
      streamRef.current?.getTracks()?.forEach(t => t.stop());
      log('🧹 Stopped all media tracks');
    } catch {}
  };

  const detachVideo = () => {
    if (videoRef.current) {
      videoRef.current.srcObject = null;
      log('🧹 Cleared video srcObject');
    }
  };

  const setupRecorder = (stream) => {
    const desiredMime = 'video/webm';
    const mime = MediaRecorder.isTypeSupported(desiredMime) ? desiredMime : '';
    const rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);

    rec.onstart = () => log('🎥 MediaRecorder onstart');
    rec.onstop = () => log('⏹️ MediaRecorder onstop');
    rec.onpause = () => log('⏸️ MediaRecorder onpause');
    rec.onresume = () => log('▶️ MediaRecorder onresume');
    rec.onerror = (e) => log('❌ MediaRecorder onerror:', e?.error || e);

    rec.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        chunksRef.current.push(e.data);           // sync buffer
        setChunks(prev => [...prev, e.data]);     // visibility only
        log('📦 ondataavailable:', (e.data.size/1024).toFixed(1), 'KB');
      }
    };
    recorderRef.current = rec;
    log('✅ MediaRecorder ready');
  };

  const startCamera = async () => {
    if (streamRef.current) return; // already on
    log('Requesting webcam…');
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    streamRef.current = stream;
    if (videoRef.current) videoRef.current.srcObject = stream;
    log('✅ Webcam stream set on video element');
    setupRecorder(stream);
  };

  const stopCamera = () => {
    try {
      const rec = recorderRef.current;
      if (rec && rec.state !== 'inactive') {
        rec.onstop = () => log('⏹️ Recorder stopped (camera off)');
        rec.stop();
      }
    } catch {}
    recorderRef.current = null;
    stopAllTracks();
    streamRef.current = null;
    detachVideo();
  };

  // --- mount/unmount guard ---
  useEffect(() => {
    return () => {
      clearInterval(intervalRef.current);
      try {
        if (recorderRef.current && recorderRef.current.state !== 'inactive') {
          recorderRef.current.stop();
        }
      } catch {}
      stopCamera();
      log('🔚 Unmounted, cleaned up.');
    };
  }, []);

  // --- react to record toggle ---
  useEffect(() => {
    (async () => {
      if (recordSession) {
        try { await startCamera(); }
        catch (e) { log('❌ getUserMedia failed:', e); }
      } else {
        stopCamera();
        chunksRef.current = [];
        setChunks([]);
        log('🎚️ Record OFF → camera and recorder stopped');
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recordSession]);

  // --- upload ---
  const uploadVideo = async () => {
    const pieces = chunksRef.current.slice();
    if (pieces.length === 0) {
      log('uploadVideo: nothing to upload (chunksRef=', pieces.length, ')');
      return;
    }
    setIsUploading(true);
    const t0 = performance.now();
    try {
      const blob = new Blob(pieces, { type: 'video/webm' });
      log('⬆️ Uploading… size=', (blob.size/1024/1024).toFixed(2), 'MB');

      // clear buffers for next run
      chunksRef.current = [];
      setChunks([]);

      const fd = new FormData();
      fd.append('video', blob, 'study_session.webm');
      fd.append('task', task);
      fd.append('task_category', taskCategory);

      const res = await fetch('/upload', {
        method: 'POST',
        headers: { 'X-User-Id': String(userId) }, // Vite proxy → same-origin
        body: fd,
      });

      const ct = res.headers.get('content-type') || '';
      const isJson = ct.includes('application/json');
      const data = isJson ? await res.json() : await res.text();

      log('HTTP', res.status, 'CT:', ct);
      if (!res.ok) {
        log('Server error payload:', typeof data === 'string' ? data.slice(0, 300) : data);
        throw new Error(`Upload failed (${res.status})`);
      }
      if (!isJson) {
        log('Expected JSON, got text:', data?.slice?.(0, 300));
        throw new Error('Server returned non-JSON');
      }

      setAnalysis(data?.pipeline_result || null);
      setLastSessionId(data?.session_id ?? null);
      log('✅ Upload+analysis ok in', ((performance.now()-t0)/1000).toFixed(2), 's');
      if (autoStatsTriggerRef.current) setStatsOpen(true);
    } catch (e) {
      log('❌ uploadVideo error:', e);
    } finally {
      autoStatsTriggerRef.current = null;
      setIsUploading(false);
    }
  };

  // --- timer controls ---
  const handleStart = () => {
    if (isRunning) return;
    setIsRunning(true);
    log('▶️ Start. recordSession=', recordSession);

    if (recordSession && recorderRef.current?.state === 'inactive') {
      chunksRef.current = [];
      setChunks([]);
      recorderRef.current.onstop = () => setTimeout(uploadVideo, 0); // ensure all chunks delivered
      recorderRef.current.start();
      log('🎥 Recording started');
    }

    intervalRef.current = setInterval(() => {
      setSecondsLeft(prev => {
        if (prev === 0) {
          clearInterval(intervalRef.current);
          setIsRunning(false);
          log('⏲️ Natural end');

          if (recordSession && recorderRef.current?.state === 'recording') {
            autoStatsTriggerRef.current = 'natural';
            recorderRef.current.onstop = () => {
              log('⏹️ Recorder stopped (natural)');
              setTimeout(uploadVideo, 0);
            };
            recorderRef.current.stop();
          }
          switchToNextMode();
          return modeSettings[getNextMode(mode)].duration;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handlePause = () => {
    clearInterval(intervalRef.current);
    setIsRunning(false);
    log('⏸️ Pause');
    if (recordSession && recorderRef.current?.state === 'recording') {
      autoStatsTriggerRef.current = null;
      recorderRef.current.onstop = () => { log('⏹️ Recorder stopped (pause)'); setTimeout(uploadVideo, 0); };
      recorderRef.current.stop();
    }
  };

  const handleEndSessionNow = () => {
    clearInterval(intervalRef.current);
    setIsRunning(false);
    log('🛑 End Session');
    if (recordSession && recorderRef.current?.state === 'recording') {
      autoStatsTriggerRef.current = 'end';
      recorderRef.current.onstop = () => {
        log('⏹️ Recorder stopped (ended early)');
        setTimeout(uploadVideo, 0);
        switchToNextMode();
      };
      recorderRef.current.stop();
    } else {
      switchToNextMode();
    }
  };

  const handleModeChange = (newMode) => {
    clearInterval(intervalRef.current);
    setIsRunning(false);
    log('🔁 Manual mode →', mode, '→', newMode);
    setMode(newMode);
    setSecondsLeft(modeSettings[newMode].duration);

    if (recordSession && recorderRef.current?.state === 'recording') {
      autoStatsTriggerRef.current = null;
      recorderRef.current.onstop = () => { log('⏹️ Recorder stopped (mode switch)'); setTimeout(uploadVideo, 0); };
      recorderRef.current.stop();
    }
  };

  // --- UI ---
  const bg = useColorModeValue(modeSettings[mode].color, modeSettings[mode].color);

  return (
    <Box bg={bg} minH="100vh" display="flex" alignItems="center" justifyContent="center" px={4}>
      <VStack spacing={6} maxW="700px" w="100%">
        <Heading size="xl">{modeSettings[mode].label}</Heading>

        <HStack w="100%" spacing={4}>
          <FormControl>
            <FormLabel>Task</FormLabel>
            <Input value={task} onChange={(e) => setTask(e.target.value)} placeholder="e.g., Calc HW Ch. 7" />
          </FormControl>
          <FormControl>
            <FormLabel>Category</FormLabel>
            <Input value={taskCategory} onChange={(e) => setTaskCategory(e.target.value)} placeholder="e.g., Math" />
          </FormControl>
        </HStack>

        {recordSession && (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            style={{ width: '420px', borderRadius: 8 }}
            onPlay={() => log('📺 Preview playing')}
          />
        )}

        <Circle size="300px" border="12px solid" borderColor="teal.400" boxShadow="0 0 40px rgba(0,128,128,0.5)" display="flex" alignItems="center" justifyContent="center">
          <Text fontSize="6xl" fontWeight="semibold">{formatTime(secondsLeft)}</Text>
        </Circle>

        <HStack spacing={4} wrap="wrap" justify="center">
          {!isRunning ? (
            <Button size="lg" colorScheme="green" onClick={handleStart}>Start</Button>
          ) : (
            <Button size="lg" colorScheme="orange" onClick={handlePause}>Pause</Button>
          )}
          <Button size="lg" colorScheme="red" variant="outline" onClick={handleEndSessionNow}>End Session</Button>

          <FormControl display="flex" alignItems="center" width="auto">
            <FormLabel htmlFor="rec-switch" mb="0">Record</FormLabel>
            <Switch
              id="rec-switch"
              isChecked={recordSession}
              onChange={(e) => setRecordSession(e.target.checked)}
            />
          </FormControl>

          <Select value={mode} onChange={(e) => handleModeChange(e.target.value)} width="180px" isDisabled={isRunning}>
            <option value="focus">Focus</option>
            <option value="shortBreak">Short Break</option>
            <option value="longBreak">Long Break</option>
          </Select>

          <Button size="md" onClick={() => setStatsOpen(true)}>View Stats</Button>
        </HStack>

        {isUploading && <Text fontSize="md">Uploading & analyzing…</Text>}

        <Modal isOpen={statsOpen} onClose={() => setStatsOpen(false)} size="lg">
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Session Statistics {lastSessionId ? `#${lastSessionId}` : ''}</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {!analysis && (<Text>{isUploading ? 'Uploading & analyzing…' : 'No analysis available yet.'}</Text>)}
              {analysis?.summary && (
                <VStack align="stretch" spacing={4}>
                  <Stat>
                    <StatLabel>Mean Focus Score</StatLabel>
                    <StatNumber>{analysis.summary.mean_focus_score}</StatNumber>
                    <StatHelpText>EMA smoothed</StatHelpText>
                  </Stat>
                  <HStack>
                    <Stat><StatLabel>% Focused</StatLabel><StatNumber>{analysis.summary.pct_focused}%</StatNumber></Stat>
                    <Stat><StatLabel>% Partial</StatLabel><StatNumber>{analysis.summary.pct_partial}%</StatNumber></Stat>
                    <Stat><StatLabel>% Unfocused</StatLabel><StatNumber>{analysis.summary.pct_unfocused}%</StatNumber></Stat>
                  </HStack>
                  <Stat>
                    <StatLabel>Longest Focused Streak</StatLabel>
                    <StatNumber>{analysis.summary.longest_focused_streak_s}s</StatNumber>
                  </Stat>
                  <Divider />
                  {Array.isArray(analysis.segments) && analysis.segments.length > 0 && (
                    <>
                      <Heading size="md">Focused Segments</Heading>
                      <VStack align="stretch" spacing={2} maxH="240px" overflowY="auto">
                        {analysis.segments.map((seg, i) => (
                          <Box key={i} p={3} borderWidth="1px" borderRadius="md">
                            <Text><b>Start:</b> {seg.start_s.toFixed?.(2) ?? seg.start_s}s</Text>
                            <Text><b>End:</b> {seg.end_s.toFixed?.(2) ?? seg.end_s}s</Text>
                            <Text><b>Duration:</b> {seg.duration_s.toFixed?.(2) ?? seg.duration_s}s</Text>
                          </Box>
                        ))}
                      </VStack>
                    </>
                  )}
                </VStack>
              )}
            </ModalBody>
            <ModalFooter><Button onClick={() => setStatsOpen(false)}>Close</Button></ModalFooter>
          </ModalContent>
        </Modal>
      </VStack>
    </Box>
  );
}

export default PomodoroTimer;
