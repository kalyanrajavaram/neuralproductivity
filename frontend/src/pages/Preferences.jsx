 import { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  Select,
  VStack,
  Heading,
  useToast,
} from '@chakra-ui/react';

function Preferences() {
  const [dailyStudyMinutes, setDailyStudyMinutes] = useState('');
  const [averageFocusMinutes, setAverageFocusMinutes] = useState('');
  const [breakPreference, setBreakPreference] = useState('');
  const [startTime, setStartTime] = useState('');
  const toast = useToast();

  const handleSubmit = () => {
    const preferencesData = {
      dailyStudyMinutes,
      averageFocusMinutes,
      breakPreference,
      startTime,
    };

    console.log('User Preferences:', preferencesData);

    // TODO: Later send this to your backend using Axios
    toast({
      title: 'Preferences Saved',
      description: 'Your personalized study plan will be generated soon!',
      status: 'success',
      duration: 3000,
      isClosable: true,
    });

    // Reset form (optional)
    setDailyStudyMinutes('');
    setAverageFocusMinutes('');
    setBreakPreference('');
    setStartTime('');
  };

  return (
    <Box
      maxW="500px"
      mx="auto"
      mt={10}
      p={6}
      boxShadow="md"
      borderRadius="lg"
      bg="gray.50"
    >
      <Heading size="lg" mb={6} textAlign="center">
        Set Your Study Preferences
      </Heading>

      <VStack spacing={4}>
        <FormControl>
          <FormLabel>Desired Study Time Per Day (in minutes)</FormLabel>
          <Input
            type="number"
            value={dailyStudyMinutes}
            onChange={(e) => setDailyStudyMinutes(e.target.value)}
          />
        </FormControl>

        <FormControl>
          <FormLabel>Average Focus Time Per Session (in minutes)</FormLabel>
          <Input
            type="number"
            value={averageFocusMinutes}
            onChange={(e) => setAverageFocusMinutes(e.target.value)}
          />
        </FormControl>

        <FormControl>
          <FormLabel>Break Preference</FormLabel>
          <Select
            placeholder="Select break type"
            value={breakPreference}
            onChange={(e) => setBreakPreference(e.target.value)}
          >
            <option value="short">Short Breaks (5 min)</option>
            <option value="long">Long Breaks (15 min)</option>
          </Select>
        </FormControl>

        <FormControl>
          <FormLabel>Preferred Study Start Time</FormLabel>
          <Input
            type="time"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
          />
        </FormControl>

        <Button colorScheme="teal" onClick={handleSubmit} width="100%">
          Save Preferences
        </Button>
      </VStack>
    </Box>
  );
}

export default Preferences;
